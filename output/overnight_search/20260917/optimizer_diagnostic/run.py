"""Four fixed, sequential warm-start diagnostics; independent of main protocols."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))

from examples.inventory.overnight_search.evaluator import NumericalSandbox, prelude
from examples.inventory.overnight_search.memory_guard import MemoryGuardMixin
from examples.inventory.overnight_search.perishable import Scenario


class DiagnosticSandbox(MemoryGuardMixin, NumericalSandbox):
    memory_limit_bytes = 1024 ** 3


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    temporary.replace(path)


BODY = r'''
prepared = prepare_policy(request['code'], None)
assert len(prepared['values']) == 6
initial = prepared['values'] if request['initialization'] == 'literal_default' else request['training_theta']
bounds = [[x['min'], x['max']] for x in prepared['opt_params'].values()]
if len(initial) != len(bounds) or any(not lo <= value <= hi for value, (lo, hi) in zip(initial, bounds)):
    raise ValueError('Invalid warm-start parameter vector')
namespace = {}
exec(compile(prepared['source'], 'diagnostic_policy.py', 'exec'), namespace)
numeric = njit(namespace['compute_order_amount'], boundscheck=True)
@njit
def policy(age, pipeline, theta, mu, cv, f, L):
    return numeric(age, pipeline, mu, cv, f, L, theta)
s = Scenario(**request['scenario'])
cap = inventory_cap(s)
settings = request['settings']
training = sample_demands(s, settings['paths'], settings['burnin'] + settings['horizon'], settings['fit_seed'])
validation = sample_demands(s, settings['paths'], settings['burnin'] + settings['horizon'], settings['validation_seed'])
def evaluate(theta, tape):
    return evaluate_kernel(policy, np.asarray(theta, dtype=float), tape, s.m, s.L, cap,
                           s.mean, s.cv, s.f, s.h, s.p, s.w, settings['burnin'])
initial_cost = []
def objective(theta):
    cost = float(evaluate(theta, training)[0].mean())
    if not initial_cost:
        initial_cost.append(cost)
    return cost
fitted = optimize(objective, bounds, initial, settings['budget'], settings['optimizer_seed'])
train_costs, train_metrics = evaluate(fitted['theta'], training)
validation_costs, validation_metrics = evaluate(fitted['theta'], validation)
answer = dict(initialization=request['initialization'], scenario=request['scenario'],
    initial_theta=list(initial), initial_train_cost=initial_cost[0], theta=fitted['theta'],
    nfev=fitted['nfev'], optimizer_seconds=fitted['seconds'],
    train_cost=float(train_costs.mean()), validation_cost=float(validation_costs.mean()),
    train_path_costs=train_costs.tolist(), validation_path_costs=validation_costs.tolist(),
    train_metrics=train_metrics.mean(axis=0).tolist(), validation_metrics=validation_metrics.mean(axis=0).tolist(),
    train_demand_sha256=hashlib.sha256(training.tobytes()).hexdigest(),
    validation_demand_sha256=hashlib.sha256(validation.tobytes()).hexdigest(),
    code_sha256=prepared['code_sha256'], structure_sha256=prepared['structure_sha256'],
    parameter_order=list(prepared['opt_params']), bounds=bounds, cap=cap,
    additional_scoring_evaluations=2,
    transitions=(fitted['nfev']+2)*settings['paths']*(settings['burnin']+settings['horizon']))
print('DIAGNOSTIC_RESULT='+json.dumps(answer,allow_nan=False))
'''


def score_job(request, frozen_prelude):
    worker = frozen_prelude + "\nrequest=" + repr(request) + "\n" + BODY
    sandbox = DiagnosticSandbox(sys.executable)
    started = time.monotonic()
    result = sandbox.run(worker, timeout_seconds=900, max_output_bytes=1_000_000)
    if result.returncode or result.timed_out:
        raise RuntimeError(result.stderr[-4000:] or str(result.to_dict()))
    records = [line.removeprefix("DIAGNOSTIC_RESULT=") for line in result.stdout.splitlines()
               if line.startswith("DIAGNOSTIC_RESULT=")]
    if len(records) != 1:
        raise ValueError("Missing or ambiguous diagnostic result")
    answer = json.loads(records[0])
    answer.update(worker_wall_seconds=time.monotonic()-started,
                  observed_peak_rss_bytes=result.observed_peak_rss_bytes,
                  request_sha256=sha(json.dumps(request, sort_keys=True)))
    return answer


def paired(first, second, seed):
    """Positive percentage favors saved-training-theta initialization."""
    x, y = np.asarray(first), np.asarray(second)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(x), size=(5000, len(x)))
    xmeans, ymeans = x[indices].mean(axis=1), y[indices].mean(axis=1)
    gains = 100 * (xmeans-ymeans) / xmeans
    lo, hi = np.percentile(gains, [2.5, 97.5])
    return dict(improvement_pct=float(100*(x.mean()-y.mean())/x.mean()),
                improvement_ci_low=float(lo), improvement_ci_high=float(hi), paths=len(x),
                bootstrap_draws=5000, seed=seed)


def main():
    source_folder = HERE.parent / "extended/search/evolution_r2/candidate_00_0"
    fit = json.loads((source_folder / "fit.json").read_text())
    code = (source_folder / "policy.py").read_text()
    if code != fit['code'] or code != json.loads((source_folder / 'source.json').read_text())['code']:
        raise ValueError('Candidate source provenance mismatch')
    frozen_prelude = prelude()
    settings = dict(paths=32, burnin=500, horizon=1000, fit_seed=18111001,
                    validation_seed=18112001, budget=1024, optimizer_seed=1731)
    scenarios = [Scenario(f'perish_m7_L2_cv{cv:g}_f0', m=7, L=2, cv=cv, f=0.) for cv in (1.5, 2.)]
    protocol = dict(label='Independent exploratory optimizer diagnostic; not main AIPS evidence',
        candidate=str(source_folder.relative_to(REPO)), code_sha256=sha(code),
        source_fit_sha256=sha((source_folder / 'fit.json').read_bytes()),
        runner_sha256=sha(Path(__file__).read_bytes()), trusted_prelude_sha256=sha(frozen_prelude),
        settings=settings, scenarios=[asdict(s) for s in scenarios],
        warm_start_thetas={s.name:fit['results'][s.name]['theta'] for s in scenarios},
        initializations=['literal_default','saved_training_theta'],
        workers=1, worker_rss_limit_bytes=1024**3, per_fit_timeout_seconds=900,
        paid_api_calls=0, main_protocol_or_selection_changed=False,
        interpretation='Warm start reuses parameters from prior training. Equal fresh diagnostic objective-call ceilings do not erase that prior computational investment.')
    protocol_path = HERE / 'protocol.json'
    if protocol_path.exists() and json.loads(protocol_path.read_text()) != protocol:
        raise ValueError('Frozen diagnostic protocol changed')
    if not protocol_path.exists():
        save(protocol_path,protocol)
        (HERE / 'candidate_raw.py').write_text(code)
        (HERE / 'trusted_prelude.py').write_text(frozen_prelude)
    results = []
    for s in scenarios:
        for initialization in protocol['initializations']:
            request = dict(code=code, scenario=asdict(s), settings=settings,
                           initialization=initialization, training_theta=protocol['warm_start_thetas'][s.name])
            path = HERE / f'{s.name}_{initialization}.json'
            print('START',s.name,initialization,flush=True)
            if path.exists():
                result=json.loads(path.read_text())
                if result['request_sha256'] != sha(json.dumps(request,sort_keys=True)):
                    raise ValueError('Existing diagnostic score request changed')
            else:
                result=score_job(request,frozen_prelude)
                save(path,result)
            results.append(result)
            print('DONE',s.name,initialization,'train',result['train_cost'],'validation',result['validation_cost'],
                  'nfev',result['nfev'],'seconds',round(result['worker_wall_seconds'],2),flush=True)
    comparisons=[]
    for index,s in enumerate(scenarios):
        cold,warm=results[2*index:2*index+2]
        assert cold['train_demand_sha256']==warm['train_demand_sha256']
        assert cold['validation_demand_sha256']==warm['validation_demand_sha256']
        assert cold['structure_sha256']==warm['structure_sha256']
        assert cold['code_sha256']==warm['code_sha256']==protocol['code_sha256']
        comparisons.append(dict(scenario=s.name,cv=s.cv,
            training_improvement_pct=100*(cold['train_cost']-warm['train_cost'])/cold['train_cost'],
            validation=paired(cold['validation_path_costs'],warm['validation_path_costs'],18113001+index)))
    gains=[row['validation']['improvement_pct'] for row in comparisons]
    if all(value>0 for value in gains):
        conclusion='两个固定诊断场景的独立验证均值均支持保留训练参数作为初始点，值得作为后续优化器方案检验；这不是主实验改进或AIPS对Baek胜利。'
    elif all(value<=0 for value in gains):
        conclusion='两个固定诊断场景均未观察到保留训练参数初始化带来的独立验证均值改善；本次诊断不支持把它作为稳定改进。'
    else:
        conclusion='保留训练参数初始化的独立验证收益不一致；目前不能把它描述为稳定改进，需要扩大独立场景与优化器随机种子检验。'
    summary=dict(created_utc=datetime.now(timezone.utc).isoformat(),protocol=protocol,comparisons=comparisons,
                 n_fits=4,total_objective_calls=sum(r['nfev'] for r in results),
                 total_worker_seconds=sum(r['worker_wall_seconds'] for r in results),
                 conclusion=conclusion,api_cost_usd=0,main_result=False)
    save(HERE/'summary.json',summary)
    lines=['# 独立优化器诊断：保留训练参数还是重置原始常数','',conclusion,'',
        '固定使用 extended/evolution_r2/candidate_00_0 的同一六参数结构，只检查 m=7、纯LIFO、CV=1.5/2 两个预先指定场景。未增加LLM调用，未改变运行中的方法、候选选择或主协议。',
        '',f"原始源码SHA256：`{protocol['code_sha256']}`。参数顺序："+', '.join(results[0]['parameter_order'])+'。',
        '', '两种初始化共享新训练种子18111001、32路径、500预热期、1000计分期、1024次目标函数上限、DE种子1731；独立验证种子18112001，路径数/时域相同。每次拟合另外进行一次训练重评分和一次验证评分，未计入优化器目标函数次数。单worker顺序运行，1 GiB内存监测，每拟合900秒保护。',
        '', '| CV | 初始化 | 新训练成本 | 独立验证成本 | nfev | 优化器秒 | worker秒 |',
        '|---|---|---:|---:|---:|---:|---:|']
    for result in results:
        lines.append(f"| {result['scenario']['cv']:g} | {result['initialization']} | {result['train_cost']:.6f} | {result['validation_cost']:.6f} | {result['nfev']} | {result['optimizer_seconds']:.2f} | {result['worker_wall_seconds']:.2f} |")
    lines+=['','| CV | 保留参数的新训练改善% | 独立验证改善% [95%配对路径区间] |','|---|---:|---:|']
    for row in comparisons:
        val=row['validation']
        lines.append(f"| {row['cv']:g} | {row['training_improvement_pct']:.3f} | {val['improvement_pct']:.3f} [{val['improvement_ci_low']:.3f}, {val['improvement_ci_high']:.3f}] |")
    lines+=['','正改善表示保留训练参数初始化更好；所有四次拟合与负结果均保留。区间仅衡量这两个固定拟合结果的验证需求路径误差，不包含优化器随机种子、结构选择或模型生成不确定性。这里只用了一个DE种子和一个候选结构，不能推断普遍性能。',
        '', 'Warm start使用了已完成训练的参数；两种方法的新诊断拟合上限相同，不代表计入原训练后总计算相同。主实验有意保留原始常数重新初始化，此处不改写主实验。',
        '', '## 参数与初始点','']
    for result in results:
        lines += [f"- CV={result['scenario']['cv']:g}, {result['initialization']}",
                  '  - 初始参数：'+json.dumps(result['initial_theta']),
                  '  - 新拟合参数：'+json.dumps(result['theta']),
                  f"  - 初始点在新训练路径上的成本：{result['initial_train_cost']:.6f}。"]
    lines += ['', '完整逐路径成本、费用分项、需求数组哈希、参数、计数和耗时保存在四份对应JSON。protocol.json冻结设置、源码和helper哈希；summary.json记录全部比较。']
    (HERE/'README.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':
    main()
