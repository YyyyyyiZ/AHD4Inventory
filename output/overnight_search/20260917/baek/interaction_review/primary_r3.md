# Baek 会话执行记录：primary_r3

模型请求 11 次；Python工具执行 10 次；累计工具时间 810.64 秒。

本文件从已保存日志只读导出模型提交的工具代码及系统实际返回值，没有重运行任何实验。每次模型请求中均只有最初那一条用户任务；后续由模型自主决定下一步工具代码。

反馈中的 stdout/stderr、返回码、超时状态及剩余预算是实际送回模型的信息。代码打印的 test/validation 是模型自行生成的开发样本，不能当作最终封存测试结果。

[最终策略](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/overnight_search/20260917/baek/sessions/l2_r3/policy.py)

<details>
<summary>初始任务提示</summary>

````text
Design a reusable algorithm for the following CLASS of perishable inventory problems.
You receive the mathematical model and broad parameter ranges, not the target evaluation instance list.
Return Python source defining design(params), which returns a stationary order function policy(age,pipeline).
Choose any algorithmic representation or parameter count. Your task is to minimize expected long-run cost.

MODEL AND OBSERVATIONS
One product has integer inventory. At a decision epoch, age is a length-m int64 array ordered by
remaining shelf life 1,2,...,m, and already includes today's receipts. pipeline is length L-1:
pipeline[k-1] is old quantity arriving k periods from now. Decide a nonnegative order q;
it arrives L periods later, with m usable periods of fresh shelf life. There are no clocks,
future-demand observations, episode indexes, or persistent policy memory. Use only current state and fixed params.
The simulator projects every method's action identically: first max(0, q), then clip to
max(0, cap - sum(age) - sum(pipeline)), then round with numpy.rint (half to even).
Thus cap constrains current inventory POSITION, not just the amount ordered or the on-hand stock.

After ordering, two independent demands are realized. Serve the FIFO group first using oldest stock first;
then serve the LIFO group using freshest stock first. Unmet demand is lost. Any remaining stock with one
usable period expires. The surviving stock ages one period; the next period's due orders then arrive fresh.
The per-period cost is w*(expired units) + p*(lost units) + h*(surviving units). No purchasing or fixed order costs.

DEMAND LAW (exact known distribution, not just moment information)
Total demand mean is mean, its standard deviation is cv*mean; cv is the ordinary coefficient of variation.
FIFO and LIFO demands are INDEPENDENT nonnegative-integer two-moment Adan--van Eenige--Resing distributions.
FIFO mean = f*mean, variance = f*(cv*mean)^2. LIFO mean = (1-f)*mean, variance = (1-f)*(cv*mean)^2.
These are not binomial shares of one sampled total demand and need not be a single negative-binomial law.
The preloaded _aer_components and aer_pmf implement the exact distribution; sample_demands samples it.
Across periods all demands are independent. No law needs to be estimated.
cap is the smallest integer q whose cumulative probability under the sum of (m+L) iid TOTAL demands
is at least p/(p+w), computed by the supplied inventory_cap. It is not a high-percentile safety limit.

PARAMETERS
The problem class has shelf life m in {3,4,5}, lead time L=2, mean=4,
ordinary demand CV cv in {1.5,2}, FIFO fraction f in {0,0.5}, h=0, p=100, w=100,
with demand_mode='paper_cv', cap_mode='paper'. These family specifications are common to all approaches.
It may also contain name, actual_cv, and inventory_cap for reporting; ignore additional reporting keys.
This is an explicitly specified extension of the Baek L2 design protocol to perishable inventory.

COMMON TRUSTED COMPUTATION PROVIDED TO EVERY TOOL CALL AND FINAL DESIGN
The following helpers are already loaded, with no access to any validation/test demands:
  Scenario(name,m,L,cv,f,mean=4,h=0,p=100,w=100,demand_mode='paper_cv',cap_mode='paper')
  scenario_from_params(params) -> Scenario
  _aer_components(mean,sd) -> (mixture weight, SciPy discrete distribution) pairs
  aer_pmf(mean,sd) -> NumPy probability mass array, tail below 1e-13 numerically removed
  inventory_cap(scenario) -> int; sample_demands(scenario,npaths,periods,seed) -> [npaths,periods,2] integer array
  evaluate_python(scenario,demands,policy,burnin=200) -> (per_path_cost_per_period,per_path_[waste,lost,order])
  training_demands(params) -> common training sample, 8 paths of 200+512 periods, seed=17091001
  simulate(policy,params,demands=None,npaths=8,burnin=200,horizon=512,seed=17091001)
      -> dict(mean_cost,path_costs,components,backend); arbitrary policy(age,pipeline) accepted.
  evaluate(scenario,demands,numba_policy,theta,burnin=200) -> same arrays as evaluate_python.
      For this fast parameterized helper only: numba_policy(age,pipeline,theta,mu,cv,f,L) returns scalar q.
  optimize(objective,bounds,initial,budget=256,seed=1) -> dict(theta,cost,nfev,seconds).
      This is the same 256-evaluation, 16-population differential-evolution helper available to the competing workflow.
You may use or replace these helpers; they do not constrain your final algorithm. numpy as np, scipy, numba.njit,
and Python standard libraries are available. TRUSTED_BENCHMARK_SOURCE contains full helper source for inspection.
Numba acceleration and shared simulator/optimizer access are explicit favorable adaptations to the original protocol.
Simulation begins empty with ordinary demand during an unscored burn-in. Default training uses 200 burn-in +512
scored periods on 8 paths; independent evaluation uses longer trajectories. You may generate your own samples.
No zero-demand stocking periods and no terminal salvage value are used.

COMPUTATION BUDGET
You have 3,600 seconds cumulative run_python execution across at most 50 calls, shared across all development
and experiments in this session. Each call is a fresh process: re-define your own variables/functions each time;
the trusted helpers are reloaded automatically. Test and revise any approach within this budget.
Final design(params) may do instance-specific computation, including simulation and optimization. Aim to finish
within 30 seconds per instance; a 600-second hang guard is used and actual setup time is recorded.
The returned policy(age,pipeline) must be lightweight, deterministic, and stationary. It must not invoke an LLM,
read files, use networking, or access future demand. Helper functions, arbitrary fixed tables, NumPy, SciPy and
Numba are allowed; there is no numerical-parameter-count limit. Final helpers provided above remain available.
Return your final complete source in one Python code block, defining design(params). No prose after the code.
````

</details>

## 工具调用 1

来自第 1 次模型请求。

模型提交的代码：

````python
for m in (3,4,5):
 for cv in (1.5,2):
  for f in (0,.5):
   p=dict(name='x',m=m,L=2,cv=cv,f=f,mean=4,h=0,p=100,w=100,demand_mode='paper_cv',cap_mode='paper')
   s=scenario_from_params(p)
   print(m,cv,f, inventory_cap(s), [len(aer_pmf(f*4,(f*(cv*4)**2)**.5)) if f else 1, len(aer_pmf((1-f)*4,((1-f)*(cv*4)**2)**.5)) if f<1 else 1])
print(TRUSTED_BENCHMARK_SOURCE[:1000])
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "3 1.5 0 17 [1, 299]\n3 1.5 0.5 16 [281, 281]\n3 2 0 14 [1, 516]\n3 2 0.5 14 [492, 492]\n4 1.5 0 21 [1, 299]\n4 1.5 0.5 20 [281, 281]\n4 2 0 18 [1, 516]\n4 2 0.5 17 [492, 492]\n5 1.5 0 25 [1, 299]\n5 1.5 0.5 24 [281, 281]\n5 2 0 22 [1, 516]\n5 2 0.5 21 [492, 492]\n\"\"\"Perishable-inventory screening model, with explicit source discrepancies.\n\nPolicy state is quantities by remaining life (oldest first) after receipt and\norders due in 1,...,L-1 periods. See docs/overnight_perishable_spec.md.\nNo API calls occur in this module.\n\"\"\"\nfrom __future__ import annotations\nfrom dataclasses import asdict, dataclass\nfrom functools import lru_cache\nfrom typing import Callable\nimport numpy as np\nfrom numba import njit\nfrom scipy import stats\n\n@dataclass(frozen=True)\nclass Scenario:\n    name: str\n    m: int\n    L: int\n    cv: float\n    f: float\n    mean: float = 4.0\n    h: float = 0.0\n    p: float = 100.0\n    w: float = 100.0\n    demand_mode: str = 'paper_cv'\n    cap_mode: str = 'paper'\n\n    @property\n    def sd(self) -> float:\n        if self.demand_mode == 'paper_cv':\n            return self.cv * self.mean\n        if self.demand_mode == 'legacy_code':\n            return self.cv * np.sqrt(self.mean)\n        raise ValueError(f'Unknown demand mode: {self.demand_mo\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 1.3754282090812922,
  "timed_out": false,
  "remaining_calls": 49,
  "remaining_seconds": 3598.6245717909187
}
````

## 工具调用 2

来自第 2 次模型请求。

模型提交的代码：

````python
i=TRUSTED_BENCHMARK_SOURCE.find('def optimize')
print(TRUSTED_BENCHMARK_SOURCE[i:i+2500])
i=TRUSTED_BENCHMARK_SOURCE.find('def evaluate(')
print(TRUSTED_BENCHMARK_SOURCE[i:i+2000])
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "def optimize(objective, bounds, initial, budget=256, seed=1):\n    bounds = np.asarray(bounds, dtype=float)\n    initial = np.asarray(initial, dtype=float)\n    start = time.monotonic()\n    nfev, best, best_x = 0, float('inf'), initial.copy()\n    class Done(Exception):\n        pass\n    def fun(x):\n        nonlocal nfev, best, best_x\n        if nfev >= budget:\n            raise Done()\n        nfev += 1\n        val = float(objective(x))\n        if not np.isfinite(val):\n            raise ValueError(\"Nonfinite simulation objective\")\n        if val < best:\n            best, best_x = val, np.asarray(x).copy()\n        return val\n    fun(initial)\n    if len(initial):\n        pop = qmc.LatinHypercube(d=len(initial), seed=seed).random(16)\n        pop = qmc.scale(pop, bounds[:, 0], bounds[:, 1])\n        pop[0] = initial\n        try:\n            differential_evolution(fun, bounds, init=pop, maxiter=budget,\n                                   mutation=(.4, 1.), recombination=.8,\n                                   rng=seed, polish=False, tol=0., atol=0.)\n        except Done:\n            pass\n    return {\"theta\": best_x.tolist(), \"cost\": best, \"nfev\": nfev,\n            \"seconds\": time.monotonic()-start}\n\n\ndef scenario_from_params(params):\n    fields = {name: params[name] for name in Scenario.__dataclass_fields__ if name in params}\n    fields.setdefault(\"name\", \"anonymous_instance\")\n    return Scenario(**fields)\n\ndef training_demands(params):\n    return sample_demands(scenario_from_params(params), 8, 200+512, 17091001)\n\ndef simulate(policy, params, demands=None, *, npaths=8, burnin=200, horizon=512, seed=17091001):\n    \"\"\"Score arbitrary scalar policy(age,pipeline); return mean and path costs.\n\n    Exact trusted transitions are used; attempts optional Numba acceleration,\n    falling back to unrestricted Python callback evaluation if compilation fails.\n    \"\"\"\n    s = scenario_from_params(params)\n    if demands is None:\n        demands = sample_demands(s, npaths, burnin+horizon, seed)\n    backend = \"python\"\n    try:\n        compiled = policy if hasattr(policy, \"py_func\") else njit(policy)\n        def adapter(age, pipeline, theta, mu, cv, f, L):\n            return compiled(age, pipeline)\n        fast = njit(adapter)\n        costs, components = evaluate(s, demands, fast, np.empty(0), burnin)\n        backend = \"numba\"\n    except Exception:\n        costs, components = evaluate_python(s, demands, policy, burnin)\n    return {\"mean_cost\": float(costs.mean()), \"path_costs\": costs,\n   \ndef evaluate(scenario: Scenario, demands: np.ndarray, policy: Callable, theta: np.ndarray, burnin: int=200):\n    return evaluate_kernel(policy, np.asarray(theta, dtype=float), demands, scenario.m, scenario.L, inventory_cap(scenario), scenario.mean, scenario.sd / scenario.mean, scenario.f, scenario.h, scenario.p, scenario.w, burnin)\n\ndef evaluate_python(scenario: Scenario, demands: np.ndarray, policy: Callable, burnin: int=200):\n    \"\"\"Reference evaluator for arbitrary policy(age,pipeline)->scalar callbacks.\n\n    Shares demand paths, transitions, integer projection, and objective with\n    evaluate(). Runtime is deliberately not restricted by the model semantics.\n    \"\"\"\n    demands = np.asarray(demands)\n    if demands.ndim != 3 or demands.shape[-1] != 2:\n        raise ValueError('Demands must have shape [paths,periods,2]')\n    npaths, periods, _ = demands.shape\n    if not 0 <= burnin < periods:\n        raise ValueError('Invalid burnin')\n    costs = np.zeros(npaths)\n    components = np.zeros((npaths, 3))\n    cap = inventory_cap(scenario)\n    for path in range(npaths):\n        age = np.zeros(scenario.m, dtype=np.int64)\n        pipeline = np.zeros(max(0, scenario.L - 1), dtype=np.int64)\n        for t in range(periods):\n            raw_order = float(policy(age.copy(), pipeline.copy()))\n            if not np.isfinite(raw_order):\n                raise ValueError('Nonfinite policy action')\n            raw_order = max(0.0, raw_order)\n            if cap >= 0:\n                raw_order = min(raw_order, max(0, cap - int(age.sum()) - int(pipeline.sum())))\n            if raw_order > 1000000000000.0:\n                raise ValueError('Numerically unsafe policy action')\n            order = int(np.rint(raw_order))\n            waste, lost, held = transition_inplace(age, pipeline, order, int(demands[path, t, 0]), int(demands[path, t, 1]), scenario.L)\n            if t >= burnin:\n                costs[path] += scenario.w * waste + scenario.p * lost + scenario.h * held\n                com\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 0.6601627920754254,
  "timed_out": false,
  "remaining_calls": 48,
  "remaining_seconds": 3597.9644089988433
}
````

## 工具调用 3

来自第 3 次模型请求。

模型提交的代码：

````python
import numpy as np, time
from numba import njit
@njit
def pol_lin(age, pipe, th, mu, cv, f, L):
    q=th[0]
    for j in range(age.size): q += th[1+j]*age[j]
    q += th[6]*pipe[0]
    return q
@njit
def pol_bs(age, pipe, th, mu, cv, f, L):
    z=th[0]
    for j in range(age.size): z-=age[j]
    z-=pipe[0]
    return z
results={}
for m in (3,4,5):
 for cv in (1.5,2.):
  for f in (0.,.5):
   params=dict(name='x',m=m,L=2,cv=cv,f=f,mean=4,h=0,p=100,w=100,demand_mode='paper_cv',cap_mode='paper')
   s=scenario_from_params(params); cap=inventory_cap(s)
   dem=sample_demands(s,16,300+1000,88101+m*1000+int(cv*10)*10+int(f*10))
   def obj(x): return evaluate(s,dem,pol_lin,x,300)[0].mean()
   init=np.array([min(cap, 4*(m+1)), -1,-1,-1,-1,-1,-1.])
   bd=[(0,35)]+[(-3,1.5)]*5+[(-3,1.5)]
   r=optimize(obj,bd,init, budget=400, seed=43)
   # independent
   test=sample_demands(s,32,500+4000,99177)
   c,comp=evaluate(s,test,pol_lin,np.array(r['theta']),500)
   # brute BS targets grid .2
   bsbest=(1e9,None)
   for S in np.arange(0,cap+0.01,.25):
    cc=evaluate(s,dem,pol_bs,np.array([S]),300)[0].mean()
    if cc<bsbest[0]:bsbest=(cc,S)
   cb,co=evaluate(s,test,pol_bs,np.array([bsbest[1]]),500)
   key=(m,cv,f); results[key]=r['theta']
   print(key,'cap',cap,'train',round(r['cost'],2),'test',round(c.mean(),2),'comp',np.round(comp.mean(0),3),'BS',bsbest,round(cb.mean(),2),'theta',np.round(r['theta'],3), 'sec',round(r['seconds'],1),flush=True)
print('RESULTS=',results)
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 1.5, 0.0) cap 17 train 235.29 test 237.07 comp [0.707 1.663 3.07 ] BS (np.float64(250.61874999999998), np.float64(10.5)) 250.39 theta [ 6.029 -0.3    0.529 -0.381 -0.78  -2.377 -0.742] sec 1.3\n(3, 1.5, 0.5) cap 16 train 206.86 test 204.58 comp [0.57  1.476 3.113] BS (np.float64(224.59375), np.float64(12.5)) 221.7 theta [ 7.502 -0.12  -0.3   -0.417 -1.671  1.147 -0.805] sec 0.7\n(3, 2.0, 0.0) cap 14 train 271.19 test 266.37 comp [0.529 2.135 2.407] BS (np.float64(284.36249999999995), np.float64(8.5)) 278.73 theta [ 7.119 -1.908  0.084 -2.511 -1.148 -1.581 -1.303] sec 0.6\n(3, 2.0, 0.5) cap 14 train 234.5 test 237.53 comp [0.457 1.918 2.577] BS (np.float64(249.76875), np.float64(10.5)) 252.09 theta [ 8.3   -0.031 -0.094 -0.847 -1.133 -0.626 -1.334] sec 0.7\n(4, 1.5, 0.0) cap 21 train 207.99 test 208.02 comp [0.747 1.333 3.441] BS (np.float64(215.28750000000002), np.float64(12.5)) 216.68 theta [14.258 -0.366 -0.492 -1.155 -1.05  -1.947 -1.267] sec 0.7\n(4, 1.5, 0.5) cap 20 train 170.29 test 176.71 comp [0.539 1.228 3.33 ] BS (np.float64(181.78125), np.float64(14.5)) 188.93 theta [ 7.387  0.018 -0.174 -0.498 -0.275  0.245 -0.599] sec 0.7\n(4, 2.0, 0.0) cap 18 train 237.11 test 240.28 comp [0.528 1.875 2.667] BS (np.float64(247.70624999999998), np.float64(10.5)) 249.4 theta [10.676 -0.948  0.    -1.507 -1.295 -0.391 -1.006] sec 0.7\n(4, 2.0, 0.5) cap 17 train 213.51 test 214.06 comp [0.438 1.702 2.773] BS (np.float64(223.6625), np.float64(10.5)) 224.23 theta [ 9.293 -0.211 -0.411 -0.759 -0.779 -0.939 -0.921] sec 0.7\n(5, 1.5, 0.0) cap 25 train 176.87 test 182.98 comp [0.558 1.272 3.313] BS (np.float64(187.375), np.float64(14.5)) 191.3 theta [16.425 -1.949  0.143 -1.899 -2.276 -1.134 -1.416] sec 0.8\n(5, 1.5, 0.5) cap 24 train 152.2 test 155.58 comp [0.411 1.145 3.284] BS (np.float64(160.16875), np.float64(14.5)) 163.98 theta [ 9.588 -0.273 -0.129 -0.442 -0.548 -0.471 -0.855] sec 0.8\n(5, 2.0, 0.0) cap 22 train 210.56 test 218.13 comp [0.524 1.658 2.879] BS (np.float64(221.375), np.float64(12.5)) 226.94 theta [13.57  -0.166  0.261 -2.523 -1.813 -1.253 -1.032] sec 0.7\n(5, 2.0, 0.5) cap 21 train 181.06 test 195.43 comp [0.418 1.536 2.919] BS (np.float64(188.00625), np.float64(12.75)) 202.08 theta [ 8.06e+00 -3.84e-01  4.00e-03 -6.90e-01 -6.42e-01 -3.33e-01 -6.44e-01] sec 0.7\nRESULTS= {(3, 1.5, 0.0): [6.029307102006401, -0.2996140541712203, 0.529271190025492, -0.3812075310642512, -0.7804418064941203, -2.3771913523442523, -0.7424379086341519], (3, 1.5, 0.5): [7.502148286353258, -0.12013552860189058, -0.2999179153575504, -0.41696516447006904, -1.6714845639205456, 1.1468729692676, -0.8045382873162465], (3, 2.0, 0.0): [7.1194209998367715, -1.9083621531893338, 0.0835577914023854, -2.5112025882486213, -1.1483277475110922, -1.5814843205739202, -1.3029268379811012], (3, 2.0, 0.5): [8.299584373292003, -0.03094350952316316, -0.0938227536116335, -0.8470626967646158, -1.1333463463060354, -0.6259929693762688, -1.3337453523990406], (4, 1.5, 0.0): [14.258499635791015, -0.36636450858786673, -0.4919477165205246, -1.1554282272442409, -1.0500510905488682, -1.9465726005736979, -1.2673600639356353], (4, 1.5, 0.5): [7.387490415735774, 0.01775565449432004, -0.1735722256359732, -0.4982404170108287, -0.2750304832047406, 0.24508353264536142, -0.5994841232384902], (4, 2.0, 0.0): [10.676145378182447, -0.9482038566534596, 7.176039717282645e-05, -1.5068864027032338, -1.2947775828321304, -0.39078050740404907, -1.0063494436971632], (4, 2.0, 0.5): [9.293174434849384, -0.2114708814762607, -0.4107677516759464, -0.7588762356079511, -0.7785632314351683, -0.9387828364989219, -0.9213971548352777], (5, 1.5, 0.0): [16.42507895847494, -1.9486755687585404, 0.14333797731519193, -1.8987222284279552, -2.2764257848886436, -1.1337450722170193, -1.4160063531152782], (5, 1.5, 0.5): [9.587707310718265, -0.2734705122554772, -0.1293903665228675, -0.4421478412864137, -0.5479182979660173, -0.47061961449874185, -0.8546767653892633], (5, 2.0, 0.0): [13.569730853974018, -0.16612503895279085, 0.2609811889754696, -2.5229692626700237, -1.8134543599195478, -1.25266621610002, -1.0319171801822065], (5, 2.0, 0.5): [8.060134020965645, -0.38410727942492084, 0.004304144556519951, -0.689660556443022, -0.641907691657122, -0.33311586578680596, -0.6444033286683102]}\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 12.57745095784776,
  "timed_out": false,
  "remaining_calls": 47,
  "remaining_seconds": 3585.3869580409955
}
````

## 工具调用 4

来自第 4 次模型请求。

模型提交的代码：

````python
import numpy as np
from numba import njit
@njit
def pol_quad(a,p,th,mu,cv,f,L):
 q=th[0]; tot=0.; old=0.; fresh=0.
 for j in range(a.size):
  x=a[j]; tot+=x; q+=th[1+j]*x
  if j<2: old+=x
  if j>=a.size-2: fresh+=x
 q+=th[6]*p[0]
 cap=th[13]
 q+=th[7]*tot*tot/cap+th[8]*old*old/cap+th[9]*fresh*fresh/cap+th[10]*tot*p[0]/cap+th[11]*old*fresh/cap
 q+=th[12]*max(0.,old-4.)
 return q
prior={
(3,1.5,0):[6.029,-.3,.529,-.381,-.78,-2.377,-.742],(3,1.5,.5):[7.502,-.12,-.3,-.417,-1.67,1.15,-.805],
(4,1.5,0):[14.258,-.366,-.492,-1.155,-1.05,-1.947,-1.267],(4,1.5,.5):[7.387,.018,-.174,-.498,-.275,.245,-.599],
(5,1.5,0):[16.425,-1.949,.143,-1.899,-2.276,-1.134,-1.416],(5,1.5,.5):[9.588,-.273,-.129,-.442,-.548,-.471,-.855],
(3,2.,0):[7.119,-1.908,.084,-2.511,-1.148,-1.581,-1.303],(3,2.,.5):[8.3,-.031,-.094,-.847,-1.133,-.626,-1.334],
(4,2.,0):[10.676,-.948,0,-1.507,-1.295,-.391,-1.006],(4,2.,.5):[9.293,-.211,-.411,-.759,-.779,-.939,-.921],
(5,2.,0):[13.57,-.166,.261,-2.523,-1.813,-1.253,-1.032],(5,2.,.5):[8.06,-.384,.004,-.69,-.642,-.333,-.644]}
for key in [(3,1.5,0),(4,1.5,.5),(5,1.5,0),(5,2,.5),(3,2,0),(4,2,.5)]:
 m,cv,f=key; params=dict(m=m,L=2,cv=cv,f=f,mean=4,h=0,p=100,w=100,demand_mode='paper_cv',cap_mode='paper');s=scenario_from_params(params);cap=inventory_cap(s)
 dem=sample_demands(s,32,300+2000,1371)
 init=np.zeros(14);init[:7]=prior[key];init[13]=cap
 def obj(x):
  xx=np.r_[x,cap]
  return evaluate(s,dem,pol_quad,xx,300)[0].mean()
 bd=[(2,25)]+[(-3,1.5)]*5+[(-2.5,.5)]+[(-5,5)]*5+[(-2,2)]
 r=optimize(obj,bd,init[:13],budget=1500,seed=77)
 th=np.r_[r['theta'],cap]
 test=sample_demands(s,64,500+5000,99933)
 cq,xq=evaluate(s,test,pol_quad,th,500)
 lin=np.r_[prior[key],np.zeros(6),cap] # layout wrong prior then zeros -> th7...
 cl,xl=evaluate(s,test,pol_quad,lin,500)
 print(key,'train',r['cost'],'quad',cq.mean(),xq.mean(0),'lin',cl.mean(),xl.mean(0),'th',np.round(th,3),flush=True)
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 1.5, 0) train 235.159375 quad 234.7603125 [0.70200625 1.64559687 3.0643375 ] lin 235.42249999999999 [0.70925    1.644975   3.07212187] th [ 7.568  0.066  0.37  -0.597 -1.669 -0.152 -0.913 -0.632 -1.349 -0.522\n  1.277  1.279  0.427 17.   ]\n(4, 1.5, 0.5) train 171.6734375 quad 177.0546875 [0.52464063 1.24590625 3.28586875] lin 177.224375 [0.54700313 1.22524062 3.328925  ] th [ 7.921e+00 -1.300e-02 -2.010e-01 -5.430e-01 -4.910e-01  2.700e-01\n -5.320e-01 -2.000e-03  3.370e-01  2.640e-01 -2.720e-01 -3.660e-01\n -5.000e-02  2.000e+01]\n(5, 1.5, 0) train 177.93437500000002 quad 179.136875 [0.63593437 1.15543438 3.4883625 ] lin 181.2115625 [0.55808438 1.25403125 3.31205313] th [16.156 -0.854 -0.35  -2.042 -1.552 -1.24  -0.985  0.789  0.06  -0.667\n  0.63  -0.103  0.34  25.   ]\n(5, 2, 0.5) train 188.4375 quad 193.39187500000003 [0.43729062 1.49662813 2.95500312] lin 193.69343750000002 [0.42077188 1.5161625  2.91891875] th [ 7.535 -0.301  0.03  -0.343 -0.272 -0.19  -0.593 -0.192  0.126 -0.28\n -0.306  0.214  0.109 21.   ]\n(3, 2, 0) train 262.0609375 quad 265.42281249999996 [0.52934375 2.12488438 2.408575  ] lin 265.6459375 [0.530725   2.12573437 2.4094625 ] th [ 6.856e+00 -1.585e+00  1.200e-02 -1.499e+00 -1.078e+00 -1.676e+00\n -1.055e+00 -1.570e-01 -1.260e-01  6.070e-01  3.249e+00  1.200e-01\n -2.200e-02  1.400e+01]\n(4, 2, 0.5) train 207.3265625 quad 211.88375000000002 [0.46343125 1.65540625 2.82239375] lin 212.62 [0.4431     1.6831     2.77431562] th [ 9.26  -0.352 -0.444 -1.076 -1.193 -1.021 -0.957  0.046 -0.177  1.015\n  0.672  0.03   0.519 17.   ]\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 52.46856000018306,
  "timed_out": false,
  "remaining_calls": 46,
  "remaining_seconds": 3532.9183980408125
}
````

## 工具调用 5

来自第 5 次模型请求。

模型提交的代码：

````python
# use Python simulate custom gather state codes for scenario m5 etc, one long demand; implement transitions helper direct trusted
import numpy as np

def gather(m,cv,f,theta,seed,n=1000000):
 s=Scenario('x',m,2,cv,f); cap=inventory_cap(s); dem=sample_demands(s,1,n,seed)[0]
 age=np.zeros(m,dtype=np.int64); pipe=np.zeros(1,dtype=np.int64); seen=set(); counts={}
 for t in range(n):
  code=tuple(age)+(int(pipe[0]),)
  seen.add(code); counts[code]=counts.get(code,0)+1
  q=theta[0]+sum(theta[1+j]*age[j] for j in range(m))+theta[6]*pipe[0]
  q=int(np.rint(min(max(0.,q),max(0,cap-age.sum()-pipe.sum()))))
  transition_inplace(age,pipe,q,int(dem[t,0]),int(dem[t,1]),2)
 return len(seen),sum(v for v in counts.values() if v>=10), sorted(counts.values(),reverse=True)[:10]
ths={(5,1.5,0):[16.425,-1.949,.143,-1.899,-2.276,-1.134,-1.416],(5,1.5,.5):[9.588,-.273,-.129,-.442,-.548,-.471,-.855],(3,2,0):[7.119,-1.908,.084,-2.511,0,0,-1.303]}
for k,t in ths.items(): print(k,gather(*k,t,8,200000))
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(5, 1.5, 0) (7754, 183489, [6099, 5605, 4219, 3978, 3460, 3442, 2863, 2729, 2647, 2489])\n(5, 1.5, 0.5) (7941, 184346, [2520, 2342, 2308, 2198, 2163, 1976, 1840, 1823, 1814, 1805])\n(3, 2, 0) (36, 200000, [39929, 20920, 18093, 15081, 12234, 9319, 8686, 6103, 5818, 5817])\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 7.315686332993209,
  "timed_out": false,
  "remaining_calls": 45,
  "remaining_seconds": 3525.6027117078193
}
````

## 工具调用 6

来自第 6 次模型请求。

模型提交的代码：

````python
import numpy as np, time
from numba import njit
@njit
def rank_state(x, comb):
 s=0; r=0
 for i in range(x.size):
  s+=x[i]; y=s+i; r+=comb[y,i+1]
 return r
@njit
def action_lin(age,pipe,th,cap):
 q=th[0]
 for j in range(age.size):q+=th[1+j]*age[j]
 q+=th[6]*pipe
 if q<0:q=0.
 avail=cap-pipe
 for j in range(age.size):avail-=age[j]
 if q>avail:q=avail
 return int(np.rint(q))
@njit
def trans(age,pipe,order,df,dl):
 # returns waste+lost and new pipe
 for j in range(age.size):
  z=min(age[j],df);age[j]-=z;df-=z
 for j in range(age.size-1,-1,-1):
  z=min(age[j],dl);age[j]-=z;dl-=z
 cost=df+dl+age[0]
 for j in range(age.size-1):age[j]=age[j+1]
 age[age.size-1]=pipe
 return cost,order
@njit
def gather_ranks(dem,m,cap,th,comb):
 n=dem.shape[0]; ranks=np.empty(n,np.int64); states=np.empty((n,m+1),np.int16)
 age=np.zeros(m,np.int64);pipe=0
 for t in range(n):
  for j in range(m):states[t,j]=age[j]
  states[t,m]=pipe;ranks[t]=rank_state(states[t],comb)
  q=action_lin(age,pipe,th,cap)
  _,pipe=trans(age,pipe,q,dem[t,0],dem[t,1])
 return ranks,states
@njit
def rollout(states,futures,th,cap):
 K=states.shape[0];R=futures.shape[0];H=futures.shape[1];m=states.shape[1]-1
 acts=np.empty(K,np.int16); gaps=np.empty(K,np.float64)
 for k in range(K):
  avail=cap
  for j in range(m+1):avail-=states[k,j]
  best=1e100;second=1e100;bq=0
  for q0 in range(avail+1):
   score=0.
   for rr in range(R):
    age=np.empty(m,np.int64)
    for j in range(m):age[j]=states[k,j]
    pipe=int(states[k,m])
    for t in range(H):
     if t==0:q=q0
     else:q=action_lin(age,pipe,th,cap)
     co,pipe=trans(age,pipe,q,int(futures[rr,t,0]),int(futures[rr,t,1]))
     score+=co
   if score<best:
    second=best;best=score;bq=q0
   elif score<second:second=score
  acts[k]=bq;gaps[k]=(second-best)/R
 return acts,gaps
# table policy evaluator njit dynamic mapping dense rank
@njit
def pol_table(age,pipe,theta,mu,cv,f,L):
 # theta: lin7, cap, comb flattened? can't table in theta floats. later custom eval kernel or global impossible
 return 0.
priors={(5,1.5,0):[16.156,-.854,-.35,-2.042,-1.552,-1.24,-.985], # quad was better can't rollout baseline quad unsupported
(5,1.5,.5):[9.588,-.273,-.129,-.442,-.548,-.471,-.855],
(4,2,.5):[9.26,-.352,-.444,-1.076,-1.193,0,-.957],
(3,2,0):[6.856,-1.585,.012,-1.499,0,0,-1.055]}
# custom Python closure evaluate test via evaluate_python
for key in [(5,1.5,.5),(5,1.5,0),(4,2,.5),(3,2,0)]:
 m,cv,f=key;s=Scenario('x',m,2,cv,f);cap=inventory_cap(s);th=np.array(priors[key],float)
 # comb
 comb=np.zeros((cap+m+2,m+2),np.int64)
 for n in range(comb.shape[0]):
  comb[n,0]=1
  for k in range(1,min(n,m+1)+1):comb[n,k]=comb[n-1,k-1]+comb[n-1,k]
 N=int(comb[cap+m,m+1]) # wait states len m+1 subsets max cap+m; total choose(cap+m+1,m+1)
 N=int(comb[cap+m+1,m+1]) if cap+m+1<comb.shape[0] else 0
 dem=sample_demands(s,1,500000,17231)[0]
 ranks,states=gather_ranks(dem,m,cap,th,comb)
 cnt=np.bincount(ranks)
 top=np.argsort(cnt)[::-1];top=top[cnt[top]>0]; cum=np.cumsum(cnt[top]);K=min(5000,np.searchsorted(cum,0.997*len(ranks))+1)
 selected=top[:K]; pos=np.full(cnt.size,-1,np.int32);pos[ranks]=np.arange(len(ranks),dtype=np.int32); st=states[pos[selected]]
 fut=sample_demands(s,512,30,883)[...]
 t=time.time();acts,gaps=rollout(st,fut,th,cap);print('rollsec',time.time()-t)
 table=np.full(cnt.size,-1,np.int16);table[selected]=acts
 # closure tuple rank using math.comb matrix
 def policy(age,pipeline, table=table,comb=comb,th=th,cap=cap):
  su=0;r=0
  for i,x in enumerate(np.r_[age,pipeline]):
   su+=int(x);r+=int(comb[su+i,i+1])
  if r<len(table) and table[r]>=0:return int(table[r])
  return th[0]+np.dot(th[1:1+len(age)],age)+th[6]*pipeline[0]
 test=sample_demands(s,32,500+3000,99119)
 cr=simulate(policy,dict(m=m,L=2,cv=cv,f=f),demands=test,burnin=500)
 def base(age,pipeline,th=th):return th[0]+np.dot(th[1:1+len(age)],age)+th[6]*pipeline[0]
 cb=simulate(base,dict(m=m,L=2,cv=cv,f=f),demands=test,burnin=500)
 print(key,'unique',len(top),'K',K,'cover',cum[K-1]/len(ranks),'changes',np.mean(acts!=np.array([action_lin(np.array(x[:-1],dtype=np.int64),int(x[-1]),th,cap) for x in st])),'gap',np.mean(gaps),'base',cb['mean_cost'],'roll',cr['mean_cost'],cr['components'].mean(0),flush=True)
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "rollsec 18.928374767303467\n(5, 1.5, 0.5) unique 9189 K 5000 cover 0.971956 changes 0.6114 gap 0.0236625 base 153.40833333333333 roll 153.17395833333333 [0.46344792 1.06829167 3.37578125]\nrollsec 20.38721776008606\n(5, 1.5, 0) unique 15965 K 5000 cover 0.9451 changes 0.6348 gap 1.9531249999999998e+94 base 178.33437500000002 roll 179.02291666666667 [0.59629167 1.1939375  3.36958333]\nrollsec 4.3843419551849365\n(4, 2, 0.5) unique 2065 K 1849 cover 0.997024 changes 0.7955651703623581 gap 0.04767674249594375 base 219.015625 roll 212.99583333333334 [0.33164583 1.7983125  2.52683333]\nrollsec 0.02751898765563965\n(3, 2, 0) unique 17 K 17 cover 1.0 changes 0.47058823529411764 gap 1.1488970588235295e+96 base 260.9375 roll 265.1270833333333 [0.65633333 1.9949375  2.62282292]\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 53.5282266670838,
  "timed_out": false,
  "remaining_calls": 44,
  "remaining_seconds": 3472.0744850407355
}
````

## 工具调用 7

来自第 7 次模型请求。

模型提交的代码：

````python
import numpy as np,time
from numba import njit
@njit
def act(a,p,th,cap):
 q=th[0]
 for j in range(a.size):q+=th[1+j]*a[j]
 q+=th[6]*p
 avail=cap-p-sum(a)
 q=max(0.,min(q,avail))
 return int(np.rint(q))
@njit
def tr(a,p,q,df,dl):
 for j in range(a.size):z=min(a[j],df);a[j]-=z;df-=z
 for j in range(a.size-1,-1,-1):z=min(a[j],dl);a[j]-=z;dl-=z
 c=df+dl+a[0]
 for j in range(a.size-1):a[j]=a[j+1]
 a[-1]=p
 return c,q
@njit
def rankst(x,C):
 su=0;r=0
 for i in range(x.size):
  su+=x[i];r+=C[su+i,i+1]
 return r
@njit
def gather(dem,m,cap,th,C):
 ranks=np.empty(len(dem),np.int64); states=np.empty((len(dem),m+1),np.int16);a=np.zeros(m,np.int64);p=0
 for t in range(len(dem)):
  for j in range(m):states[t,j]=a[j]
  states[t,m]=p;ranks[t]=rankst(states[t],C)
  q=act(a,p,th,cap);_,p=tr(a,p,q,dem[t,0],dem[t,1])
 return ranks,states
@njit
def paired(states,fut,th,cap):
 K=states.shape[0];R=fut.shape[0];H=fut.shape[1];m=states.shape[1]-1; out=np.empty(K,np.int16);adv=np.empty(K)
 for k in range(K):
  aa=np.empty(m,np.int64)
  for j in range(m):aa[j]=states[k,j]
  pp=int(states[k,m]);qb=act(aa,pp,th,cap)
  avail=cap-pp-sum(aa);best=0.;bestq=qb
  for q0 in range(avail+1):
   if q0==qb:continue
   delta=0.
   for r in range(R):
    a=np.empty(m,np.int64);b=np.empty(m,np.int64)
    for j in range(m):a[j]=states[k,j];b[j]=states[k,j]
    p=int(states[k,m]);pb=p
    for t in range(H):
     qa=q0 if t==0 else act(a,p,th,cap)
     qbb=qb if t==0 else act(b,pb,th,cap)
     ca,p=tr(a,p,qa,int(fut[r,t,0]),int(fut[r,t,1]));cb,pb=tr(b,pb,qbb,int(fut[r,t,0]),int(fut[r,t,1]));delta+=ca-cb
     same=p==pb
     if same:
      for j in range(m):
       if a[j]!=b[j]:same=False;break
     if same:break
   delta/=R
   # require 0.01 unit benefit, tie base
   if delta<best-0.01:best=delta;bestq=q0
  out[k]=bestq;adv[k]=best
 return out,adv
priors={(5,1.5,0):[16.425,-1.949,.143,-1.899,-2.276,-1.134,-1.416],(5,1.5,.5):[9.588,-.273,-.129,-.442,-.548,-.471,-.855],(4,2,.5):[9.293,-.211,-.411,-.759,-.779,0,-.921],(3,2,0):[7.119,-1.908,.084,-2.511,0,0,-1.303],(3,1.5,.5):[7.502,-.12,-.3,-.417,0,0,-.805]}
for key in priors:
 m,cv,f=key;s=Scenario('x',m,2,cv,f);cap=inventory_cap(s);th=np.array(priors[key]); C=np.zeros((cap+m+2,m+2),np.int64)
 for n in range(len(C)):
  C[n,0]=1
  for j in range(1,min(n,m+1)+1):C[n,j]=C[n-1,j-1]+C[n-1,j]
 dem=sample_demands(s,1,500000,17231)[0];ranks,states=gather(dem,m,cap,th,C);cnt=np.bincount(ranks);top=np.flatnonzero(cnt);top=top[np.argsort(cnt[top])[::-1]];cum=np.cumsum(cnt[top]);K=min(6000,np.searchsorted(cum,.995*len(ranks))+1);sel=top[:K];pos=np.full(len(cnt),-1,np.int32);pos[ranks]=np.arange(len(ranks));st=states[pos[sel]]
 fut=sample_demands(s,512,80,883);tt=time.time();actions,ad=paired(st,fut,th,cap);print('sec',time.time()-tt)
 tab=np.full(len(cnt),-1,np.int16);tab[sel]=actions
 def policy(age,pipeline,tab=tab,C=C,th=th):
  x=list(age)+list(pipeline);su=0;r=0
  for i,v in enumerate(x):su+=int(v);r+=int(C[su+i,i+1])
  if r<len(tab) and tab[r]>=0:return int(tab[r])
  return th[0]+np.dot(th[1:1+len(age)],age)+th[6]*pipeline[0]
 def base(age,pipeline,th=th):return th[0]+np.dot(th[1:1+len(age)],age)+th[6]*pipeline[0]
 for seed in [99119,77113]:
  test=sample_demands(s,64,500+5000,seed); cb=simulate(base,dict(m=m,L=2,cv=cv,f=f),test,burnin=500);ct=simulate(policy,dict(m=m,L=2,cv=cv,f=f),test,burnin=500);print(key,seed,'base',cb['mean_cost'],'tab',ct['mean_cost'],ct['components'].mean(0))
 print('K',K,'cover',cum[K-1]/len(ranks),'change',np.mean(actions!=np.array([act(np.array(x[:-1],dtype=np.int64),int(x[-1]),th,cap) for x in st])),'adv',ad.mean(),flush=True)
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "sec 50.14264106750488\n(5, 1.5, 0) 99119 base 182.0265625 tab 182.3671875 [0.66059375 1.16307813 3.50416563]\n(5, 1.5, 0) 77113 base 180.3753125 tab 180.70937500000002 [0.66265937 1.14443438 3.5065625 ]\nK 6000 cover 0.988788 change 0.84 adv -0.42739453125\nsec 17.912033081054688\n(5, 1.5, 0.5) 99119 base 155.97843749999998 tab 156.98781250000002 [0.37898437 1.19089375 3.21012812]\n(5, 1.5, 0.5) 77113 base 154.62937499999998 tab 155.5828125 [0.38089687 1.17493125 3.21063125]\nK 6000 cover 0.98554 change 0.38133333333333336 adv -0.014526041666666666\nsec 2.6679797172546387\n(4, 2, 0.5) 99119 base 210.9034375 tab 210.5384375 [0.40325    1.70213437 2.70244062]\n(4, 2, 0.5) 77113 base 210.080625 tab 209.770625 [0.40425    1.69345625 2.70144375]\nK 1753 cover 0.995014 change 0.3502567027952082 adv -0.019747397318881917\nsec 0.07946014404296875\n(3, 2, 0) 99119 base 265.30156250000005 tab 269.578125 [0.44539375 2.2503875  2.20357813]\n(3, 2, 0) 77113 base 265.611875 tab 269.93375000000003 [0.442275  2.2570625 2.20315  ]\nK 33 cover 0.996844 change 0.09090909090909091 adv -0.005385890151515152\nsec 0.11768507957458496\n(3, 1.5, 0.5) 99119 base 205.15781249999998 tab 205.436875 [0.51620313 1.53816563 3.        ]\n(3, 1.5, 0.5) 77113 base 203.73 tab 204.0446875 [0.51790937 1.5225375  3.        ]\nK 127 cover 0.99501 change 0.33858267716535434 adv -0.013625738188976378\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 117.22703695902601,
  "timed_out": false,
  "remaining_calls": 43,
  "remaining_seconds": 3354.8474480817094
}
````

## 工具调用 8

来自第 8 次模型请求。

模型提交的代码：

````python
import numpy as np,time,math
from numba import njit
@njit
def choose(n,k):
 if k<0 or k>n:return 0
 if k>n-k:k=n-k
 z=1
 for j in range(1,k+1):z=z*(n-k+j)//j
 return z
@njit
def ptab(a,p,th,mu,cv,f,L):
 su=0;r=0
 for i in range(a.size):
  su+=a[i];r+=choose(su+i,i+1)
 su+=p[0];i=a.size;r+=choose(su+i,i+1)
 v=th[7+r]
 if v>=0:return v
 q=th[0]
 for j in range(a.size):q+=th[1+j]*a[j]
 q+=th[6]*p[0]
 return q
# gather Python trajectory states using helper transition
priors={(3,2.,0):[7.119,-1.908,.084,-2.511,0,0,-1.303],(4,2.,.5):[9.293,-.211,-.411,-.759,-.779,0,-.921],(5,1.5,.5):[9.588,-.273,-.129,-.442,-.548,-.471,-.855]}
for key in priors:
 m,cv,f=key;s=Scenario('x',m,2,cv,f);cap=inventory_cap(s);N=math.comb(cap+m+1,m+1);theta=np.full(7+N,-1.,float);theta[:7]=priors[key]
 # compile and training
 dem=sample_demands(s,32,500+3000,44881)
 basecost=evaluate(s,dem,ptab,theta,500)[0].mean()
 # extract top states baseline from separate python 300k
 d=sample_demands(s,1,300000,1231)[0];age=np.zeros(m,np.int64);pipe=np.zeros(1,np.int64);cnt={};represent={}
 for t in range(len(d)):
  x=tuple(age)+(int(pipe[0]),);cnt[x]=cnt.get(x,0)+1;represent[x]=x
  q=priors[key][0]+sum(priors[key][1+j]*age[j] for j in range(m))+priors[key][6]*pipe[0];q=int(np.rint(min(max(0,q),cap-age.sum()-pipe[0])));transition_inplace(age,pipe,q,int(d[t,0]),int(d[t,1]),2)
 top=sorted(cnt,key=cnt.get,reverse=True)[:100 if m>3 else 50]
 tt=time.time();changes=0;nfev=0
 for pas in range(2):
  for x in top:
   # rank
   su=0;r=0
   for i,v in enumerate(x):su+=v;r+=math.comb(su+i,i+1)
   idx=7+r; old=theta[idx]
   # current projected action using policy raw then projection
   if old>=0:cur=int(old)
   else:
    raw=theta[0]+sum(theta[1+j]*x[j] for j in range(m))+theta[6]*x[m];cur=int(np.rint(min(max(0,raw),cap-sum(x))))
   avail=cap-sum(x); best=basecost;bv=old
   # only cur +/- 2, and maybe all for m3
   qs=range(avail+1) if m==3 else range(max(0,cur-2),min(avail,cur+2)+1)
   for q in qs:
    if q==cur:continue
    theta[idx]=q;c=evaluate(s,dem,ptab,theta,500)[0].mean();nfev+=1
    if c<best-0.001:best=c;bv=q
   theta[idx]=bv
   if bv!=old:changes+=1;basecost=best
  print(key,'pass',pas,'cost',basecost,'changes',changes)
 # test
 for seed in [99119,77113]:
  test=sample_demands(s,64,500+5000,seed);ct=evaluate(s,test,ptab,theta,500)[0].mean();tb=theta.copy();tb[7:]=-1;cb=evaluate(s,test,ptab,tb,500)[0].mean();print('test',seed,cb,ct)
 print('sec',time.time()-tt,'nfev',nfev,'N',N,flush=True)
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 2.0, 0) pass 0 cost 260.578125 changes 4\n(3, 2.0, 0) pass 1 cost 260.578125 changes 4\ntest 99119 265.30156250000005 265.16218749999996\ntest 77113 265.611875 265.5046875\nsec 5.941365003585815 nfev 392 N 3060\n(4, 2.0, 0.5) pass 0 cost 205.81979166666667 changes 32\n(4, 2.0, 0.5) pass 1 cost 205.74479166666669 changes 40\ntest 99119 210.89187500000003 210.7775\ntest 77113 210.0765625 210.06093750000002\nsec 11.294426918029785 nfev 762 N 26334\n(5, 1.5, 0.5) pass 0 cost 152.55208333333334 changes 44\n(5, 1.5, 0.5) pass 1 cost 152.46249999999998 changes 53\ntest 99119 155.97843749999998 156.18156249999998\ntest 77113 154.62937499999998 154.77031250000002\nsec 12.638160228729248 nfev 783 N 593775\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 41.36321904184297,
  "timed_out": false,
  "remaining_calls": 42,
  "remaining_seconds": 3313.4842290398665
}
````

## 工具调用 9

来自第 9 次模型请求。

模型提交的代码：

````python
import numpy as np,time
from numba import njit
@njit
def pq(a,p,th,mu,cv,f,L):
 q=th[0];tot=0.;old=0.;fresh=0.
 for j in range(a.size):
  x=a[j];q+=th[1+j]*x;tot+=x
  if j<2:old+=x
  if j>=a.size-2:fresh+=x
 q+=th[6]*p[0];cap=th[13]
 q+=(th[7]*tot*tot+th[8]*old*old+th[9]*fresh*fresh+th[10]*tot*p[0]+th[11]*old*fresh)/cap+th[12]*max(0.,old-4.)
 return q
priors={(3,1.5,0):[6.029,-.3,.529,-.381,-1,-1,-.742],(3,1.5,.5):[7.502,-.12,-.3,-.417,-1,-1,-.805],(3,2.,0):[7.119,-1.908,.084,-2.511,-1,-1,-1.303],(3,2.,.5):[8.3,-.031,-.094,-.847,-1,-1,-1.334],(4,1.5,0):[14.258,-.366,-.492,-1.155,-1.05,-1,-1.267],(4,1.5,.5):[7.387,.018,-.174,-.498,-.275,-1,-.599],(4,2.,0):[10.676,-.948,0,-1.507,-1.295,-1,-1.006],(4,2.,.5):[9.293,-.211,-.411,-.759,-.779,-1,-.921],(5,1.5,0):[16.425,-1.949,.143,-1.899,-2.276,-1.134,-1.416],(5,1.5,.5):[9.588,-.273,-.129,-.442,-.548,-.471,-.855],(5,2.,0):[13.57,-.166,.261,-2.523,-1.813,-1.253,-1.032],(5,2.,.5):[8.06,-.384,.004,-.69,-.642,-.333,-.644]}
res={}
for m in (3,4,5):
 for cv in (1.5,2.):
  for f in (0.,.5):
   key=(m,cv,f);s=Scenario('x',m,2,cv,f);cap=inventory_cap(s)
   dem=sample_demands(s,48,400+3500,310071+m*71+int(cv*10)+int(f*100))
   # map compact x [b, m age, pipe, six nonlinear] to th
   def expand(x):
    th=np.zeros(14);th[0]=x[0];th[1:1+m]=x[1:1+m];th[6]=x[1+m];th[7:13]=x[2+m:8+m];th[13]=cap;return th
   ini=np.r_[priors[key][0],priors[key][1:1+m],priors[key][6],np.zeros(6)]
   def obj(x):return evaluate(s,dem,pq,expand(x),400)[0].mean()
   # first robust linear optimize by fixing nonlinear effectively use separate compact function but bounds zeros unsupported; use optimize  m+2 and expand zeros
   def explin(x): return expand(np.r_[x,np.zeros(6)])
   def objlin(x):return evaluate(s,dem,pq,explin(x),400)[0].mean()
   inil=ini[:m+2]; bdl=[(2,25)]+[(-3,.8)]*m+[(-2.5,.2)]
   rl=optimize(objlin,bdl,inil,budget=700,seed=177)
   ini=np.r_[rl['theta'],np.zeros(6)]
   bd=bdl+[(-3,3)]*5+[(-2,2)]
   rq=optimize(obj,bd,ini,budget=1800,seed=277)
   # heldout
   test=sample_demands(s,96,500+7000,987631)
   cl,xl=evaluate(s,test,pq,explin(np.array(rl['theta'])),500)
   cq,xq=evaluate(s,test,pq,expand(np.array(rq['theta'])),500)
   chosen=rq if cq.mean()<cl.mean() else {'theta':np.r_[rl['theta'],np.zeros(6)].tolist()}
   res[key]=expand(np.array(chosen['theta'])).tolist()
   print(key,'train LQ',round(rl['cost'],3),round(rq['cost'],3),'test',round(cl.mean(),3),round(cq.mean(),3),'comps',np.round(xl.mean(0),3),np.round(xq.mean(0),3),'th',np.round(expand(np.array(chosen['theta'])),3),flush=True)
print('RES=',repr(res))
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 1.5, 0.0) train LQ 231.512 231.512 test 234.311 234.311 comps [0.711 1.632 3.077] [0.711 1.632 3.077] th [ 8.15   0.117  0.355 -0.955  0.     0.    -0.905  0.     0.     0.\n  0.     0.     0.    17.   ]\n(3, 1.5, 0.5) train LQ 204.224 204.182 test 204.606 204.545 comps [0.598 1.448 3.157] [0.601 1.444 3.163] th [ 6.379e+00 -6.200e-02 -2.890e-01 -2.720e-01  0.000e+00  0.000e+00\n -5.970e-01  2.000e-03 -8.700e-02  1.900e-02 -2.400e-02 -1.400e-02\n  2.090e-01  1.600e+01]\n(3, 2.0, 0.0) train LQ 263.127 263.127 test 264.575 264.575 comps [0.488 2.158 2.333] [0.488 2.158 2.333] th [ 6.99  -2.099  0.06  -2.485  0.     0.    -1.331  0.     0.     0.\n  0.     0.     0.    14.   ]\n(3, 2.0, 0.5) train LQ 231.808 231.772 test 234.989 234.983 comps [0.468 1.882 2.596] [0.467 1.882 2.595] th [ 8.137 -0.109 -0.253 -0.811  0.     0.    -1.236  0.042  0.496  0.015\n -0.158 -0.032 -0.355 14.   ]\n(4, 1.5, 0.0) train LQ 203.73 203.302 test 203.335 203.218 comps [0.633 1.4   3.23 ] [0.649 1.383 3.263] th [13.443 -0.231 -0.208 -1.616 -1.142  0.    -1.115  0.191  0.188 -0.138\n  0.207  0.057 -0.128 21.   ]\n(4, 1.5, 0.5) train LQ 176.296 176.243 test 176.488 176.491 comps [0.532 1.232 3.307] [0.523 1.241 3.289] th [ 7.496 -0.044 -0.195 -0.445 -0.303  0.    -0.624  0.     0.     0.\n  0.     0.     0.    20.   ]\n(4, 2.0, 0.0) train LQ 235.138 235.014 test 237.241 237.303 comps [0.558 1.815 2.746] [0.557 1.816 2.744] th [11.185 -0.224  0.051 -1.526 -1.185  0.    -1.108  0.     0.     0.\n  0.     0.     0.    18.   ]\n(4, 2.0, 0.5) train LQ 208.339 208.326 test 210.858 210.855 comps [0.447 1.662 2.795] [0.448 1.661 2.797] th [ 7.44e+00 -1.00e-01 -2.62e-01 -4.63e-01 -5.21e-01  0.00e+00 -7.47e-01\n  2.00e-03 -1.60e-02  9.00e-03 -6.00e-03  1.60e-02 -2.20e-02  1.70e+01]\n(5, 1.5, 0.0) train LQ 180.839 180.749 test 178.658 178.669 comps [0.582 1.205 3.375] [0.575 1.212 3.36 ] th [14.985  0.083  0.067 -1.564 -1.36  -1.049 -1.031  0.     0.     0.\n  0.     0.     0.    25.   ]\n(5, 1.5, 0.5) train LQ 152.949 152.882 test 154.711 154.694 comps [0.479 1.068 3.417] [0.479 1.068 3.417] th [ 9.943e+00 -1.330e-01 -3.260e-01 -5.700e-01 -4.810e-01 -5.160e-01\n -7.500e-01 -0.000e+00  1.110e-01  2.900e-02  5.000e-03 -5.700e-02\n  4.500e-02  2.400e+01]\n(5, 2.0, 0.0) train LQ 216.771 216.443 test 216.057 215.468 comps [0.502 1.659 2.847] [0.496 1.659 2.84 ] th [13.439  0.049 -0.04  -1.856 -1.42  -1.067 -1.191  0.178 -0.229 -0.334\n  0.35  -0.552  0.028 22.   ]\n(5, 2.0, 0.5) train LQ 189.187 189.17 test 192.137 192.139 comps [0.417 1.505 2.922] [0.417 1.505 2.922] th [ 6.637 -0.162 -0.082 -0.481 -0.353 -0.255 -0.53   0.     0.     0.\n  0.     0.     0.    21.   ]\nRES= {(3, 1.5, 0.0): [8.150211434411805, 0.1172106138650264, 0.35529320154322397, -0.9549218729636076, 0.0, 0.0, -0.9052916065455863, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 17.0], (3, 1.5, 0.5): [6.378612144489342, -0.06197636650442062, -0.2891722125600472, -0.2717641452671786, 0.0, 0.0, -0.5966630821875468, 0.001714431977584141, -0.08652817080424047, 0.01929811304427953, -0.02364854517174486, -0.013514317537166032, 0.20866535143221965, 16.0], (3, 2.0, 0.0): [6.990303049717867, -2.0993800341422513, 0.059756088445642286, -2.485256081630862, 0.0, 0.0, -1.3314477594785203, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 14.0], (3, 2.0, 0.5): [8.136974834906072, -0.10892173813478156, -0.25331881657159894, -0.8108894478916249, 0.0, 0.0, -1.2360430288999777, 0.04185943163525918, 0.4961570623932112, 0.014615517268405265, -0.15829926551129703, -0.03197458000237563, -0.3552928653440277, 14.0], (4, 1.5, 0.0): [13.443481011787213, -0.23069655945633694, -0.20765406862733515, -1.6156026985773435, -1.1421583482950515, 0.0, -1.1151807297837442, 0.1910705455966999, 0.18791043146824649, -0.13751956152536438, 0.2067543995332466, 0.05668224499018737, -0.12763558405309938, 21.0], (4, 1.5, 0.5): [7.496442497868013, -0.04368250573808963, -0.1952858773017624, -0.4449249339923397, -0.3027786349991175, 0.0, -0.6235731687614752, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 20.0], (4, 2.0, 0.0): [11.184996406325594, -0.22425481160010297, 0.05109617460950022, -1.5256985248109194, -1.1852700862538543, 0.0, -1.108394324398774, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 18.0], (4, 2.0, 0.5): [7.440420244941026, -0.1003518859969541, -0.26202985048240657, -0.4625672693179569, -0.5212393242101979, 0.0, -0.7468937702752043, 0.002286857621091931, -0.015997963124049663, 0.00851131482272982, -0.006499446817157084, 0.015510317376999039, -0.02198678671791998, 17.0], (5, 1.5, 0.0): [14.985033542468202, 0.08261079056175702, 0.0671691334486395, -1.564158148833873, -1.3603098231999426, -1.0494288650317474, -1.0312321100981974, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 25.0], (5, 1.5, 0.5): [9.943276415694879, -0.13337396324041373, -0.32615987508606403, -0.5701061078457158, -0.480510787930449, -0.5162252834288565, -0.7496507810938605, -0.00013129131656286486, 0.11117069072017727, 0.028592935002425213, 0.0047388912956534135, -0.056944904903380444, 0.04535780930870814, 24.0], (5, 2.0, 0.0): [13.439442842847706, 0.04891262251169093, -0.040231329552409045, -1.856168731801396, -1.4201177078258094, -1.0667919271132411, -1.1905670432543765, 0.17802330530636912, -0.22906226525164808, -0.3342621524832662, 0.35044803432808047, -0.5515185783194357, 0.02828327676906639, 22.0], (5, 2.0, 0.5): [6.636525332966319, -0.1615529553466134, -0.08220529348266004, -0.48080234602061556, -0.3527935809930218, -0.2547883799426198, -0.5302085424791921, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 21.0]}\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 505.9412877080031,
  "timed_out": false,
  "remaining_calls": 41,
  "remaining_seconds": 2807.5429413318634
}
````

## 工具调用 10

来自第 10 次模型请求。

模型提交的代码：

````python
# condensed load robust dict via paste literal
import numpy as np
from numba import njit
@njit
def pp(a,p,t,mu,cv,f,L):
 q=t[0];tot=0.;old=0.;fresh=0.
 for j in range(a.size):
  x=a[j];q+=t[1+j]*x;tot+=x
  if j<2:old+=x
  if j>=a.size-2:fresh+=x
 q+=t[6]*p[0];q+=(t[7]*tot*tot+t[8]*old*old+t[9]*fresh*fresh+t[10]*tot*p[0]+t[11]*old*fresh)/t[13]+t[12]*max(0.,old-4.)
 return q
R={
(3,1.5,0):[8.1502,.1172,.3553,-.9549,0,0,-.9053,0,0,0,0,0,0,17],(3,1.5,.5):[6.3786,-.062,-.2892,-.2718,0,0,-.5967,.0017,-.0865,.0193,-.0236,-.0135,.2087,16],(3,2.,0):[6.9903,-2.0994,.0598,-2.4853,0,0,-1.3314,0,0,0,0,0,0,14],(3,2.,.5):[8.137,-.1089,-.2533,-.8109,0,0,-1.236,.0419,.4962,.0146,-.1583,-.032,-.3553,14],
(4,1.5,0):[13.4435,-.2307,-.2077,-1.6156,-1.1422,0,-1.1152,.1911,.1879,-.1375,.2068,.0567,-.1276,21],(4,1.5,.5):[7.4964,-.0437,-.1953,-.4449,-.3028,0,-.6236,0,0,0,0,0,0,20],(4,2.,0):[11.185,-.2243,.0511,-1.5257,-1.1853,0,-1.1084,0,0,0,0,0,0,18],(4,2.,.5):[7.4404,-.1004,-.262,-.4626,-.5212,0,-.7469,.0023,-.016,.0085,-.0065,.0155,-.022,17],
(5,1.5,0):[14.985,.0826,.0672,-1.5642,-1.3603,-1.0494,-1.0312,0,0,0,0,0,0,25],(5,1.5,.5):[9.9433,-.1334,-.3262,-.5701,-.4805,-.5162,-.7497,-.0001,.1112,.0286,.0047,-.0569,.0454,24],(5,2.,0):[13.4394,.0489,-.0402,-1.8562,-1.4201,-1.0668,-1.1906,.178,-.2291,-.3343,.3504,-.5515,.0283,22],(5,2.,.5):[6.6365,-.1616,-.0822,-.4808,-.3528,-.2548,-.5302,0,0,0,0,0,0,21]}
for key,v in R.items():
 m,cv,f=key;s=Scenario('x',m,2,cv,f);t=np.array(v,float);dem=sample_demands(s,64,400+5000,601117); vals=[]
 for z in np.arange(-.8,.801,.1):
  tt=t.copy();tt[0]+=z;vals.append(evaluate(s,dem,pp,tt,400)[0].mean())
 z=np.arange(-.8,.801,.1)[np.argmin(vals)]; tt=t.copy();tt[0]+=z
 test=sample_demands(s,96,500+7000,72913);c0=evaluate(s,test,pp,t,500)[0].mean();c1=evaluate(s,test,pp,tt,500)[0].mean()
 print(key,'z',round(z,2),'train gain',round(vals[8]-min(vals),3),'test',round(c0,3),round(c1,3))
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 1.5, 0) z 0.2 train gain 0.1 test 234.698 234.692\n(3, 1.5, 0.5) z -0.0 train gain 0.0 test 203.939 203.939\n(3, 2.0, 0) z -0.4 train gain 0.0 test 263.555 263.555\n(3, 2.0, 0.5) z 0.1 train gain 0.015 test 235.46 235.479\n(4, 1.5, 0) z -0.1 train gain 0.088 test 203.749 203.746\n(4, 1.5, 0.5) z 0.1 train gain 0.031 test 175.972 176.0\n(4, 2.0, 0) z -0.0 train gain 0.0 test 236.031 236.031\n(4, 2.0, 0.5) z -0.1 train gain 0.003 test 211.207 211.213\n(5, 1.5, 0) z -0.3 train gain 0.063 test 178.826 178.95\n(5, 1.5, 0.5) z 0.2 train gain 0.063 test 154.184 154.18\n(5, 2.0, 0) z -0.0 train gain 0.0 test 214.282 214.282\n(5, 2.0, 0.5) z -0.1 train gain 0.011 test 192.634 192.685\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 18.179398874985054,
  "timed_out": false,
  "remaining_calls": 40,
  "remaining_seconds": 2789.3635424568783
}
````
