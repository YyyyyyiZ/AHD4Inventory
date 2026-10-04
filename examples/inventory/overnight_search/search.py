"""Matched one-query, independent sampling and feedback-evolution screening."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import time

import numpy as np

from ..correlated_benchmark.api_client import atomic_json
from .client import SearchClient
from .evaluator import evaluate

RUN = Path(__file__).resolve().parents[3]/'output/overnight_search/20260917'
CONFIG = dict(model='openai/gpt-5.6-sol', reasoning='high',
              llm_budget_allocation_usd=35, baek_allocation_usd=12, unallocated_usd=3,
              n_repeats=3, candidates_per_arm=8, one_query_candidates=4,
              discovery_m=[3,5], transfer_m=[4], cv=[1.5,2.], fifo=[0.,.5], L=2,
              train=dict(paths=8,burnin=200,horizon=512,seed=17091001,budget=256),
              validation=dict(paths=32,burnin=500,horizon=1000,seed=17092001),
              refit=dict(paths=32,burnin=500,horizon=1000,seed=17093001,budget=768),
              test=dict(paths=128,burnin=500,horizon=3000,seed=17094001),
              parameter_count_limit=None,
              selection='training only during search; validation chooses final structure within each arm before test',
              interpretation='exploratory family screen; algorithm-generation repetitions are 3, not number of paths',
              optimizer='common derivative-free differential evolution; exact objective-call ceiling',
              baek='tool-enabled L2 protocol adaptation; 50 tools/3600s maximum, separately measured resources')

PROBLEM = '''Design a stationary ordering policy class for single-product PERISHABLE lost-sales inventory.
The numerical optimizer tunes your annotated constants separately for each instance.
We compare designs fairly; seek low long-run cost rather than a desired winner.
Known parameters: mean demand mu=4, actual coefficient of variation cv in {1.5,2.0},
shelf life m in {3,4,5}, deterministic lead L=2, FIFO demand share f in {0,0.5}.
Holding cost 0, lost-unit penalty 100, expired-unit penalty 100, no order cost.
Each period: receive fresh order placed L periods ago; observe age and pipeline;
order q; serve FIFO customers oldest first, then LIFO customers youngest first;
expire remaining oldest units; shift ages. New order arrives in L periods.
age[i] is available stock with remaining lifetime i+1, oldest first, length m.
pipeline[j] arrives in j+1 periods, length L-1; current arrival already in age[-1].
FIFO and LIFO demand are INDEPENDENT streams, iid over periods, with group
means g*mu and variances g*(mu*cv)^2 for g=f and g=1-f. Each stream uses the
Adan--van Eenige--Resing two-moment discrete distribution. For these high-CV
instances each nonzero stream is a mixture of two geometric laws on 0,1,...:
for stream mean M and variance V, a=V/M^2-1/M >=1; b=1+a+sqrt(a*a-1),
c=1+a-sqrt(a*a-1); weight1=1/b; geometric1 success prob=2/(2+M*b),
geometric2 success prob=2/(2+M*c). Zero-mean stream is identically zero.
This is not binomial splitting of total demand and not a single negative binomial.
Actions are rounded half-to-even, then clipped to [0,max(0,cap-sum(age)-sum(pipeline))].
cap is the p/(p+w)=0.5 quantile of total demand over m+L periods
(the paper's newsvendor inventory-position cap; same for all policies).
Objective: expected mean cost after burnin. No finite selling-season or time index.
Training uses independent paths; evaluation uses different unseen demand paths.
The same function must support the full m/cv/f family. No exact test instances are disclosed.

Return ONLY Python code defining compute_order_amount(age, pipeline, mu, cv, f, L).
Return nonnegative finite scalar. Use numpy as np or math; built-in numeric operations,
bounded for loops, local numerical arrays and if statements allowed. No helper functions,
recursion, while, external side effects, random numbers, imports except math/numpy, files or network.
Each tunable constant is a literal assignment INSIDE the function, with this exact comment:
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
There is NO LIMIT on number of tunable parameters. Choose meaningful finite ranges yourself.
Do not use +=; do not call array methods. Use len(age) for m.
All eligible candidates receive the SAME derivative-free optimizer and evaluation budget.
Avoid scipy in the per-period policy: this numerical subset is shared by all three structure arms.
The separate unrestricted tool-enabled Baek baseline can use arbitrary NumPy/SciPy designs.
Do not implement your own optimizer inside the ordering function.
'''


def seed_codes():
    prefix='def compute_order_amount(age, pipeline, mu, cv, f, L):\n'
    return {
      'constant':prefix+'    C = 3.0 # OPT_PARAM: {"type":"float","initial":3.0,"min":0.0,"max":15.0}\n    return C\n',
      'base_stock':prefix+'    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}\n    return max(0.0, S-sum(age)-sum(pipeline))\n',
      'capped_base_stock':prefix+'    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}\n    C = 5.0 # OPT_PARAM: {"type":"float","initial":5.0,"min":0.0,"max":20.0}\n    return max(0.0,min(C,S-sum(age)-sum(pipeline)))\n',
      'age_discount':prefix+'    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}\n    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}\n    a = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}\n    effective = 0.0\n    for i in range(len(age)):\n        effective = effective + age[i]*min(1.0,((i+1.0)/len(age))**a)\n    return max(0.0,min(C,S-effective-sum(pipeline)))\n'
    }


def scenario_list(discovery=True):
    from .perishable import scenarios
    return [asdict(s) for s in scenarios() if (s.m in [3,5]) == discovery]


def job(code, phase='train', specs=None, **kwargs):
    settings=CONFIG[phase].copy()
    return dict(op='fit' if phase in ('train','refit') else 'evaluate', code=code,
                scenarios=specs if specs is not None else scenario_list(), optimizer_seed=1731,
                **settings, **kwargs)


def extract(text):
    blocks = re.findall(r'```(?:python)?\s*\n(.*?)```',text,re.S)
    answer=[x.strip()+'\n' for x in blocks if 'def compute_order_amount' in x]
    if not answer and 'def compute_order_amount' in text:
        start=re.search(r'^(?:import |from |def )',text,re.M)
        if start: answer=[text[start.start():].strip()+'\n']
    return answer


def score(record, denominators):
    return float(np.mean([r['cost']/denominators[s] for s,r in record['results'].items()]))


def candidate(folder, code, denominators):
    folder.mkdir(parents=True,exist_ok=True)
    cached=None
    if (folder/'fit.json').exists():
        cached=json.loads((folder/'fit.json').read_text())
        if cached.get('code')!=code:
            raise ValueError('Immutable candidate fit source changed')
    if (folder/'source.json').exists():
        if json.loads((folder/'source.json').read_text()).get('code')!=code:
            raise ValueError('Immutable candidate source record changed')
    if (folder/'policy.py').exists() and (folder/'policy.py').read_text()!=code:
        raise ValueError('Immutable candidate policy source changed')
    if cached is not None:
        return cached
    atomic_json(folder/'source.json',dict(code=code))
    (folder/'policy.py').write_text(code)
    try:
        r=evaluate(job(code))
        r.update(valid=True, score=score(r,denominators), code=code)
    except Exception as exc:
        r=dict(valid=False,error=str(exc)[-3500:],code=code)
    atomic_json(folder/'fit.json',r)
    return r


def initialize():
    RUN.mkdir(parents=True,exist_ok=True)
    target=RUN/'protocol.json'
    if target.exists() and json.loads(target.read_text()) != CONFIG:
        raise ValueError('Prospective protocol mismatch')
    atomic_json(target,CONFIG)
    bases={}
    for name, code in seed_codes().items():
        p=RUN/'baselines'/name/'fit.json'
        if p.exists():
            r=json.loads(p.read_text())
        else:
            r=evaluate(job(code))
            r.update(code=code,valid=True)
            atomic_json(p,r)
            (p.parent/'policy.py').write_text(code)
        bases[name]=r
        print('baseline',name,{s:round(x['cost'],3) for s,x in r['results'].items()},flush=True)
    den={s:min(r['results'][s]['cost'] for r in bases.values()) for s in bases['constant']['results']}
    for r in bases.values(): r['score']=score(r,den)
    return den,bases


def run_arm(arm, repeat, denominators, bases):
    client=SearchClient(RUN/'framework_budget')
    folder=RUN/'search'/f'{arm}_r{repeat}'
    folder.mkdir(parents=True,exist_ok=True)
    if (folder/'completed.json').exists(): return json.loads((folder/'completed.json').read_text())
    # Identical common baseline fallback for every arm, identified separately in output.
    seed_name=min(bases,key=lambda x:bases[x]['score'])
    pool=[dict(bases[seed_name],origin='common_baseline:'+seed_name)]
    calls=1 if arm=='one_query' else CONFIG['candidates_per_arm']
    for index in range(calls):
        raw=folder/f'call_{index:02d}.json'
        if raw.exists(): response=json.loads(raw.read_text())['content']
        else:
            prompt=PROBLEM
            if arm=='one_query':
                n=CONFIG['one_query_candidates']
                prompt+=f'\nIn this SINGLE response propose {n} distinct strong policy classes. Give {n} separate Python fences, one self-contained function in each.\n'
            elif arm=='evolution':
                elite=sorted([r for r in pool if r['valid']],key=lambda x:x['score'])[:3]
                prompt+='\nImprove the following best policy structures, or propose a substantively different promising structure. Scores are training mean cost ratios to common baselines (smaller is better).\n'
                for r in elite:
                    prompt+=f'\nScore {r["score"]:.6f}; tuned instance costs '+json.dumps({s:round(x['cost'],3) for s,x in r['results'].items()})+'\n'+r['code']
                    if CONFIG.get('feedback_details',False):
                        prompt+='\nTuned parameters and mean [waste,lost,order] per period: '+json.dumps({
                            s:dict(theta=x['theta'],metrics=x['metrics']) for s,x in r['results'].items()})+'\n'
            else:
                prompt+='\nIndependently propose ONE strong policy class. No results from prior candidates are available.\n'
            response,usage=client.chat([dict(role='user',content=prompt)],
                            max_tokens=32768,
                            metadata=dict(arm=arm,repeat=repeat,index=index))
            atomic_json(raw,dict(content=response,usage=usage))
        codes=extract(response)
        if not codes:
            atomic_json(folder/f'invalid_{index:02d}.json',dict(error='No policy code block',response=response))
        for k,code in enumerate(codes[:CONFIG['one_query_candidates'] if arm=='one_query' else 1]):
            r=candidate(folder/f'candidate_{index:02d}_{k}',code,denominators)
            r['origin']=str((folder/f'candidate_{index:02d}_{k}').relative_to(RUN))
            pool.append(r)
            print(arm,repeat,index,k,('score='+str(round(r['score'],6))) if r['valid'] else 'invalid '+r['error'][-300:],flush=True)
    answer=dict(arm=arm,repeat=repeat,pool=pool,
                best_training=min([r for r in pool if r['valid']],key=lambda x:x['score']),
                completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
    atomic_json(folder/'completed.json',answer)
    return answer


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--repeats',type=int,default=3)
    args=parser.parse_args()
    den,bases=initialize()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(run_arm,arm,r,den,bases):(arm,r) for r in range(1,args.repeats+1)
                 for arm in ('one_query','best_of_n','evolution')}
        for future in as_completed(futures):
            try:
                result=future.result()
                print('COMPLETED',result['arm'],result['repeat'],result['best_training']['score'],flush=True)
            except Exception as exc:
                atomic_json(RUN/'errors'/('_'.join(map(str,futures[future]))+'.json'),dict(error=str(exc)))
                print('ARM ERROR',futures[future],str(exc),flush=True)
    atomic_json(RUN/'framework_budget_summary.json',SearchClient(RUN/'framework_budget').summary())


if __name__=='__main__': main()
