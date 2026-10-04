"""Select with validation, refit on separate training paths, freeze, then test."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time

from ..correlated_benchmark.api_client import atomic_json
from .evaluator import evaluate
from .perishable import scenarios
from .search import RUN, CONFIG, job, score, seed_codes


def saved_evaluate(path, request):
    fingerprint=hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()
    if path.exists():
        result=json.loads(path.read_text())
        if result['request_sha256']!=fingerprint: raise ValueError('Immutable evaluation changed')
        return result
    guard=3600 if request['op']=='fit' else 900
    result=evaluate(request,timeout=guard)
    result['worker_guard_seconds']=guard
    result['request_sha256']=fingerprint
    atomic_json(path,result)
    return result


def validate(code, theta, label):
    key=hashlib.sha256((code+json.dumps(theta,sort_keys=True)).encode()).hexdigest()[:20]
    return saved_evaluate(RUN/'validation'/f'{key}.json',job(code,'validation',theta=theta))


def select_one(completed, denominators):
    arm=completed['arm']; rep=completed['repeat']
    target=RUN/'selected'/f'{arm}_r{rep}.json'
    if target.exists(): return json.loads(target.read_text())
    choices=[]
    for r in completed['pool']:
        if not r['valid']: continue
        theta={s:x['theta'] for s,x in r['results'].items()}
        v=validate(r['code'],theta,r['origin'])
        choices.append(dict(code=r['code'],origin=r['origin'],validation=score(v,denominators),
                            train_score=r['score'],train_theta=theta,
                            structure_sha256=r['structure_sha256']))
    best=min(choices,key=lambda x:x['validation'])
    result=dict(arm=arm,repeat=rep,selected=best,choices=choices)
    atomic_json(target,result)
    print('SELECTED',arm,rep,best['origin'],best['validation'],flush=True)
    return result


def _refit(code):
    key=hashlib.sha256(code.encode()).hexdigest()[:20]
    target=RUN/'refit'/f'{key}.json'
    request=job(code,'refit',specs=[asdict(s) for s in scenarios()])
    fingerprint=hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()
    if target.exists():
        result=json.loads(target.read_text())
        if result['request_sha256']!=fingerprint: raise ValueError('Immutable refit changed')
        return result
    # Each scenario already resets demand and optimizer seeds independently.
    # Checkpoint that same computation by scenario so a long family refit is
    # not discarded merely because the aggregate exceeds one worker's guard.
    parts=[]
    for spec in request['scenarios']:
        partial=dict(request,scenarios=[spec])
        parts.append(saved_evaluate(RUN/'refit_parts'/key/f"{spec['name']}.json",partial))
    combined={k:parts[0][k] for k in ('parameters','structure_sha256','code_sha256','import_normalization')
              if k in parts[0]}
    for part in parts[1:]:
        if any(part.get(k)!=v for k,v in combined.items()):
            raise ValueError('Refit scenario implementations differ')
    combined.update(results={name:row for part in parts for name,row in part['results'].items()},
                    wall_seconds=sum(part['wall_seconds'] for part in parts),
                    transitions=sum(part['transitions'] for part in parts),
                    request_sha256=fingerprint,
                    execution='Independent scenario checkpoints; unchanged seeds and objective-call ceilings',
                    per_scenario_worker_guard_seconds=3600,
                    actual_part_guards_seconds={name:part.get('worker_guard_seconds',900)
                        for part in parts for name in part['results']},
                    action_cache_by_scenario={name:part.get('action_cache', {'enabled': False})
                        for part in parts for name in part['results']})
    atomic_json(target,combined)
    return combined


def refit(code):
    import fcntl
    key=hashlib.sha256(code.encode()).hexdigest()[:20]
    directory=RUN/'refit_locks'
    directory.mkdir(parents=True,exist_ok=True)
    with (directory/f'{key}.lock').open('a+') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
        return _refit(code)


def require_completed_searches(completed):
    expected={(arm,repeat) for arm in ('one_query','best_of_n','evolution') for repeat in (1,2,3)}
    observed={(row.get('arm'),row.get('repeat')) for row in completed}
    if len(completed)!=9 or observed!=expected:
        raise ValueError('Need exactly all nine arm/repetition pairs before final selection')


def _main(freeze_only=False):
    completed=[json.loads(p.read_text()) for p in sorted((RUN/'search').glob('*/completed.json'))]
    require_completed_searches(completed)
    bases={}
    for p in sorted((RUN/'baselines').glob('*/fit.json')):
        r=json.loads(p.read_text())
        theta={s:x['theta'] for s,x in r['results'].items()}
        v=validate(r['code'],theta,p.parent.name)
        bases[p.parent.name]=dict(code=r['code'],validation=v)
    den={s:min(r['validation']['results'][s]['cost'] for name,r in bases.items() if name in seed_codes())
         for s in next(iter(bases.values()))['validation']['results']}
    with ThreadPoolExecutor(max_workers=3) as pool:
        selected=list(pool.map(lambda x:select_one(x,den),completed))
    artifacts={f'{r["arm"]}_r{r["repeat"]}':r['selected']['code'] for r in selected}
    artifacts.update({f'baseline_{name}':r['code'] for name,r in bases.items()})
    fits={}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(refit,code):name for name,code in artifacts.items()}
        for future in as_completed(futures):
            name=futures[future]
            fits[name]=future.result()
            print('REFIT',name,flush=True)
    freeze=dict(created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                artifacts={name:dict(code=code,code_sha256=hashlib.sha256(code.encode()).hexdigest(),
                    theta={s:r['theta'] for s,r in fits[name]['results'].items()}) for name,code in artifacts.items()})
    seal=RUN/'numeric_policies_freeze.json'
    if seal.exists():
        old=json.loads(seal.read_text())
        if old['artifacts']!=freeze['artifacts']: raise ValueError('Frozen policies changed')
    else: atomic_json(seal,freeze)
    if freeze_only:
        print('NUMERIC POLICIES FROZEN; final test remains sealed',flush=True)
        return
    # Seal every unrestricted comparator before any final-test tape is made.
    baek_hashes={}
    for repeat in (1,2,3):
        source=RUN/'baek'/'sessions'/f'l2_r{repeat}'/'policy.py'
        if not source.exists():
            raise ValueError(f'Final test remains sealed: Baek draw {repeat} is not frozen')
        baek_hashes[str(repeat)]=hashlib.sha256(source.read_bytes()).hexdigest()
    baek_seal=RUN/'baek_policies_freeze.json'
    if baek_seal.exists():
        if json.loads(baek_seal.read_text())['sha256']!=baek_hashes:
            raise ValueError('Frozen Baek source changed')
    else:
        atomic_json(baek_seal,dict(sha256=baek_hashes,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
    def test_one(name, artifact):
        result=saved_evaluate(RUN/'test'/f'{name}.json',job(artifact['code'],'test',
                              specs=[asdict(s) for s in scenarios()],theta=artifact['theta']))
        # The raw generated parameter values quantify optimizer contribution.
        # Score the actual literal defaults emitted by the model.
        import ast
        initials=[]
        for line in artifact['code'].splitlines():
            if 'OPT_PARAM:' in line:
                assignment=ast.parse(line.split('#',1)[0].strip()).body[0]
                initials.append(float(ast.literal_eval(assignment.value)))
        raw_theta={s.name:initials for s in scenarios()}
        raw=saved_evaluate(RUN/'test'/f'{name}_without_tuning.json',job(artifact['code'],'test',
                            specs=[asdict(s) for s in scenarios()],theta=raw_theta))
        print('TEST',name,flush=True)
        return name,result
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda item:test_one(*item),freeze['artifacts'].items()))
    atomic_json(RUN/'numeric_evaluation_completed.json',dict(policy_count=len(freeze['artifacts']),
                 test_settings=CONFIG['test'],discovery_instances=8,transfer_instances=4))


def main(freeze_only=False):
    import fcntl
    # Prevent a training-only precomputation and final scorer from duplicating
    # the same refits when the last Baek source finishes in the meantime.
    with (RUN/'.numeric_evaluation.lock').open('a+') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
        return _main(freeze_only)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--freeze-only',action='store_true')
    main(parser.parse_args().freeze_only)
