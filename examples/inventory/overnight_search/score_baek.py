"""Final isolated scoring of all frozen L2 draws on the shared test trajectories."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time

from ..correlated_benchmark.api_client import atomic_json
from .baek_perishable import DEFAULT_RUN, score_code
from .perishable import scenarios, sample_demands
from .search import RUN, CONFIG


def validate_cached_score(record, code_sha256, test_settings):
    if record.get('code_sha256')!=code_sha256 or record.get('test_settings')!=test_settings:
        raise ValueError('Immutable Baek score source or test settings changed')
    return record


def main():
    # No adaptive structure-generation process may still be using final results.
    if not (RUN/'numeric_policies_freeze.json').exists():
        raise ValueError('Freeze numerical policy classes/parameters before opening shared test')
    policies={}
    for r in range(1,4):
        source=DEFAULT_RUN/'sessions'/f'l2_r{r}'/'policy.py'
        if not source.exists(): raise ValueError(f'Missing Baek draw {r}')
        code=source.read_text()
        policies[r]=code
    freeze={str(r):hashlib.sha256(code.encode()).hexdigest() for r,code in policies.items()}
    seal=RUN/'baek_policies_freeze.json'
    if seal.exists() and json.loads(seal.read_text())['sha256']!=freeze:
        raise ValueError('Baek frozen source changed')
    if not seal.exists():
        atomic_json(seal,dict(sha256=freeze,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
    settings=CONFIG['test']
    def one(r,s):
        target=RUN/'baek_scores'/f'r{r}'/f'{s.name}.json'
        if target.exists():
            record=validate_cached_score(json.loads(target.read_text()),freeze[str(r)],settings)
            return r,s.name,record
        tapes=sample_demands(s,settings['paths'],settings['burnin']+settings['horizon'],settings['seed'])
        result=score_code(policies[r],asdict(s),tapes,burnin=settings['burnin'])
        record=dict(cost=result['mean_cost'],path_costs=result['path_costs'],
                    metrics=__import__('numpy').mean(result['components'],axis=0).tolist(),
                    setup_seconds=result['setup_seconds'],score_seconds=result['score_seconds'],
                    backend=result['backend'],code_sha256=freeze[str(r)],test_settings=dict(settings))
        atomic_json(target,record)
        print('BAEK TEST',r,s.name,round(record['cost'],5),'setup',round(record['setup_seconds'],2),flush=True)
        return r,s.name,record
    results={r:{} for r in policies}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(one,r,s):(r,s.name) for r in policies for s in scenarios()}
        for future in as_completed(futures):
            try:
                r,name,record=future.result(); results[r][name]=record
            except Exception as exc:
                r,name=futures[future]
                atomic_json(RUN/'baek_score_errors'/f'r{r}_{name}.json',dict(error=str(exc)))
                print('BAEK SCORE ERROR',r,name,str(exc)[-1000:],flush=True)
    for r,records in results.items():
        atomic_json(RUN/'test'/f'baek_r{r}.json',dict(results=records,complete=len(records)==12,
                                                  policy_sha256=freeze[str(r)]))


if __name__=='__main__': main()
