# Baek 会话执行记录：primary_r1

模型请求 19 次；Python工具执行 18 次；累计工具时间 3215.30 秒。

本文件从已保存日志只读导出模型提交的工具代码及系统实际返回值，没有重运行任何实验。每次模型请求中均只有最初那一条用户任务；后续由模型自主决定下一步工具代码。

反馈中的 stdout/stderr、返回码、超时状态及剩余预算是实际送回模型的信息。代码打印的 test/validation 是模型自行生成的开发样本，不能当作最终封存测试结果。

[最终策略](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/overnight_search/20260917/baek/sessions/l2_r1/policy.py)

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
for m in [3,4,5]:
 for cv in [1.5,2]:
  for f in [0,.5]:
   s=Scenario('x',m,2,cv,f)
   print(m,cv,f, inventory_cap(s), len(aer_pmf(f*4,(f*(cv*4)**2)**.5)) if f else 1, len(aer_pmf((1-f)*4,((1-f)*(cv*4)**2)**.5)))
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "3 1.5 0 17 1 299\n3 1.5 0.5 16 281 281\n3 2 0 14 1 516\n3 2 0.5 14 492 492\n4 1.5 0 21 1 299\n4 1.5 0.5 20 281 281\n4 2 0 18 1 516\n4 2 0.5 17 492 492\n5 1.5 0 25 1 299\n5 1.5 0.5 24 281 281\n5 2 0 22 1 516\n5 2 0.5 21 492 492\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 0.8532568749506027,
  "timed_out": false,
  "remaining_calls": 49,
  "remaining_seconds": 3599.1467431250494
}
````

## 工具调用 2

来自第 2 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np, time
@njit
def pol(age,pipeline,th,mu,cv,f,L):
    z=th[0]-th[1]*pipeline[0]
    for i in range(age.size): z-=th[2+i]*age[i]
    return z
for m in [3,4,5]:
 for cv in [1.5,2.0]:
  for f in [0.,.5]:
   pa={'name':'x','m':m,'L':2,'cv':cv,'f':f,'mean':4,'h':0,'p':100,'w':100,'demand_mode':'paper_cv','cap_mode':'paper'}
   s=scenario_from_params(pa); d=training_demands(pa)
   def obj(x): return evaluate(s,d,pol,np.array(x),200)[0].mean()
   cap=inventory_cap(s)
   init=np.r_[cap*.7, np.ones(m+1)]
   res=optimize(obj, [(0,cap)]+[(0,2)]*(m+1), init, budget=256, seed=10+m*100+int(cv*10)+int(f*2))
   print((m,cv,f,cap),round(res['cost'],3),np.round(res['theta'],3),res['seconds'])
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 1.5, 0.0, 17) 233.008 [11.124  1.178  0.074  0.413  1.069] 0.846532457973808\n(3, 1.5, 0.5, 16) 213.696 [6.921 0.397 0.517 0.135 0.569] 0.11629162495955825\n(3, 2.0, 0.0, 14) 259.668 [10.194  1.327  0.068  0.194  1.257] 0.11240216600708663\n(3, 2.0, 0.5, 14) 236.914 [4.715 0.151 0.032 0.215 0.437] 0.11028366698883474\n(4, 1.5, 0.0, 21) 201.05 [12.135  1.152  0.02   0.061  1.651  1.042] 0.11324562481604517\n(4, 1.5, 0.5, 20) 187.842 [12.772  1.227  0.339  0.612  0.705  0.9  ] 0.11308529204688966\n(4, 2.0, 0.0, 18) 232.764 [12.933  1.099  0.638  0.343  1.69   1.251] 0.114268708974123\n(4, 2.0, 0.5, 17) 215.698 [11.044  1.331  0.176  0.457  0.7    1.203] 0.11588566703721881\n(5, 1.5, 0.0, 25) 175.317 [16.575  0.914  0.682  0.125  1.931  1.845  1.767] 0.11726354085840285\n(5, 1.5, 0.5, 24) 165.503 [12.835  1.27   0.326  0.274  0.452  0.2    0.867] 0.11715795891359448\n(5, 2.0, 0.0, 22) 211.06 [16.523  1.152  0.637  0.639  1.608  1.816  1.433] 0.11781641701236367\n(5, 2.0, 0.5, 21) 198.462 [12.81   1.289  1.248  0.342  1.204  0.704  0.981] 0.11745758284814656\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 3.0463370410725474,
  "timed_out": false,
  "remaining_calls": 48,
  "remaining_seconds": 3596.100406083977
}
````

## 工具调用 3

来自第 3 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np,time
@njit
def pol(age,pipeline,th,mu,cv,f,L):
 z=th[0]-th[1]*pipeline[0]
 for i in range(age.size): z-=th[2+i]*age[i]
 return z
for m,cv,f in [(3,1.5,0),(3,1.5,.5),(5,1.5,0),(5,1.5,.5)]:
 pa=dict(name='x',m=m,L=2,cv=cv,f=f,mean=4,h=0,p=100,w=100,demand_mode='paper_cv',cap_mode='paper')
 s=scenario_from_params(pa); cap=inventory_cap(s)
 d=sample_demands(s,32,2248,12345)
 def obj(x):return evaluate(s,d,pol,np.asarray(x),200)[0].mean()
 t=time.time();res=optimize(obj,[(0,cap)]+[(0,2)]*(m+1),np.r_[.6*cap,np.ones(m+1)],budget=1024,seed=33)
 dt=time.time()-t
 de=sample_demands(s,128,5200,98765)
 c=evaluate(s,de,pol,res['theta'],200)
 print((m,cv,f), 'train',res['cost'],'test',c[0].mean(),'se',c[0].std()/np.sqrt(128),'comp',c[1].mean(0),'th',np.round(res['theta'],3),'sec',dt)
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 1.5, 0) train 235.15777587890625 test 233.47875 se 0.5514111314072684 comp [0.63733281 1.69745469 2.93530625] th [8.699e+00 1.442e+00 1.481e+00 1.000e-03 1.188e+00] sec 2.740111827850342\n(3, 1.5, 0.5) train 204.13818359375 test 203.87156249999998 se 0.5585826532715537 comp [0.58335781 1.45535781 3.13443125] th [7.28  0.76  0.161 0.132 0.451] sec 5.9513840675354\n(5, 1.5, 0) train 178.09295654296875 test 177.96437500000002 se 0.4824433225242548 comp [0.56910469 1.21053906 3.35344844] th [16.092  1.125  0.12   0.059  1.713  1.555  1.173] sec 6.118156909942627\n(5, 1.5, 0.5) train 154.58221435546875 test 154.293125 se 0.5202404903952398 comp [0.48641719 1.05651406 3.43631719] th [10.077  0.668  0.147  0.252  0.605  0.378  0.652] sec 6.144032716751099\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 22.589440957875922,
  "timed_out": false,
  "remaining_calls": 47,
  "remaining_seconds": 3573.510965126101
}
````

## 工具调用 4

来自第 4 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np,time
@njit
def pproj(age,pipeline,th,mu,cv,f,L):
 m=age.size; K=(th.size-(m+1))//4
 vals=np.empty(m,np.float64)
 for i in range(m): vals[i]=0.
 st=np.empty(m,np.int64)
 # th params: S, beta m then flattened demand
 off=m+1
 for k in range(K):
  for i in range(m):st[i]=age[i]
  # periods t, t+1
  for tt in range(2):
   df=int(th[off+4*k+2*tt]); dl=int(th[off+4*k+2*tt+1])
   # fifo
   for i in range(m):
    z=min(df,st[i]);st[i]-=z;df-=z
   # lifo
   for ii in range(m):
    i=m-1-ii;z=min(dl,st[i]);st[i]-=z;dl-=z
   # age and receipt first period only. after second just age to pre-arrival
   for i in range(m-1):st[i]=st[i+1]
   st[m-1]=pipeline[0] if tt==0 else 0
  for i in range(m):vals[i]+=st[i]
 z=th[0]
 for i in range(m):z-=th[1+i]*vals[i]/K
 return z

for m,cv,f in [(3,1.5,0),(3,1.5,.5),(5,1.5,0),(5,1.5,.5)]:
 pa=dict(name='x',m=m,L=2,cv=cv,f=f,mean=4,h=0,p=100,w=100,demand_mode='paper_cv',cap_mode='paper')
 s=scenario_from_params(pa);cap=inventory_cap(s)
 dp=sample_demands(s,64,2,991).reshape(-1).astype(float)
 d=sample_demands(s,32,2248,12345)
 def obj(x): return evaluate(s,d,pproj,np.r_[x,dp],200)[0].mean()
 res=optimize(obj,[(0,cap)]+[(0,2)]*m,np.r_[.6*cap,np.ones(m)],budget=768,seed=34)
 de=sample_demands(s,128,5200,98765)
 out=evaluate(s,de,pproj,np.r_[res['theta'],dp],200)
 print((m,cv,f),'tr',res['cost'],'test',out[0].mean(),'comp',out[1].mean(0),'th',np.round(res['theta'],3))
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 1.5, 0) tr 234.79766845703125 test 233.125 comp [0.66824062 1.66300937 3.0002    ] th [6.265 1.232 1.556 1.624]\n(3, 1.5, 0.5) tr 204.1900634765625 test 203.83984375 comp [0.58787344 1.450525   3.14376563] th [5.298 0.737 0.86  0.394]\n(5, 1.5, 0) tr 179.443359375 test 179.21125 comp [0.62707031 1.16504219 3.45694062] th [10.991  1.997  1.974  1.331  0.965  0.493]\n(5, 1.5, 0.5) tr 154.57000732421875 test 154.1284375 comp [0.49388906 1.04739531 3.45292813] th [7.045 0.571 0.528 0.612 0.816 0.444]\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 264.08572333306074,
  "timed_out": false,
  "remaining_calls": 46,
  "remaining_seconds": 3309.42524179304
}
````

## 工具调用 5

来自第 5 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np,time
@njit
def quadpol(age,pipeline,th,mu,cv,f,L):
 m=age.size;d=m+1; z=th[0]; x=pipeline[0]
 z-=th[1]*x+th[1+d]*x*x/mu
 for i in range(m):
  x=age[i];z-=th[2+i]*x+th[2+d+i]*x*x/mu
 return z
@njit
def linpol(age,pipeline,th,mu,cv,f,L):
 z=th[0]-th[1]*pipeline[0]
 for i in range(age.size):z-=th[2+i]*age[i]
 return z
for m,cv,f in [(3,1.5,0),(3,1.5,.5),(5,1.5,0),(5,1.5,.5)]:
 pa=dict(name='x',m=m,L=2,cv=cv,f=f,mean=4,h=0,p=100,w=100,demand_mode='paper_cv',cap_mode='paper');s=scenario_from_params(pa);cap=inventory_cap(s)
 d=sample_demands(s,48,2248,12345)
 def obj(x):return evaluate(s,d,quadpol,np.asarray(x),200)[0].mean()
 dd=m+1; ini=np.r_[.6*cap,np.ones(dd),np.zeros(dd)]
 res=optimize(obj,[(0,cap)]+[(0,2)]*dd+[(-2,2)]*dd,ini,budget=2048,seed=45)
 de=sample_demands(s,128,5200,98765);out=evaluate(s,de,quadpol,res['theta'],200)
 print((m,cv,f),res['cost'],out[0].mean(),out[1].mean(0),np.round(res['theta'],2))
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 1.5, 0) 232.10042317708334 233.80906249999998 [0.67497344 1.66311719 3.00651719] [10.02  0.07  0.69  0.72  0.23  1.05 -1.38 -0.35  0.51]\n(3, 1.5, 0.5) 204.13716634114584 204.28328125 [0.60201719 1.44081563 3.16763906] [ 8.18  0.66  1.19  0.31  1.2  -0.1  -1.51 -0.21 -0.46]\n(5, 1.5, 0) 177.2735595703125 178.8371875 [0.59196562 1.19640625 3.39041563] [15.75  1.47  1.22  1.24  0.1   1.96  0.44 -0.12 -0.77 -0.81  1.12 -0.17\n  0.24]\n(5, 1.5, 0.5) 153.61735026041666 154.64453125 [0.51368437 1.03276094 3.48736094] [10.97  1.21  0.86  0.42  0.83  0.56  0.69 -0.26 -0.75 -0.34 -0.35 -0.14\n -0.13]\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 68.87676145881414,
  "timed_out": false,
  "remaining_calls": 45,
  "remaining_seconds": 3240.548480334226
}
````

## 工具调用 6

来自第 6 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np,time
@njit
def tabpol(age,pipeline,th,mu,cv,f,L):
 cap=int(th[0]); z=th[1]; z+=th[2+int(pipeline[0])]
 off=2+cap+1
 for i in range(age.size):
  z+=th[off+i*(cap+1)+int(age[i])]
 return z
@njit
def lin(age,pipeline,th,mu,cv,f,L):
 z=th[0]-th[1]*pipeline[0]
 for i in range(age.size):z-=th[i+2]*age[i]
 return z
m,cv,f=5,1.5,.5
pa=dict(name='x',m=m,L=2,cv=cv,f=f,mean=4,h=0,p=100,w=100,demand_mode='paper_cv',cap_mode='paper');s=scenario_from_params(pa);cap=inventory_cap(s)
d=sample_demands(s,64,2248,12345)
def objl(x):return evaluate(s,d,lin,np.asarray(x),200)[0].mean()
r=optimize(objl,[(0,cap)]+[(0,2)]*(m+1),np.r_[.5*cap,np.ones(m+1)],budget=1024,seed=4)
# theta cap,intercept, tables pipe and ages
t=np.zeros(2+(m+1)*(cap+1));t[0]=cap;t[1]=r['theta'][0]
for j,a in enumerate(r['theta'][1:]):
 t[2+j*(cap+1):2+(j+1)*(cap+1)]=-a*np.arange(cap+1)
def obj(t):return evaluate(s,d,tabpol,t,200)[0].mean()
best=obj(t);print('start',best,r['theta'])
rng=np.random.default_rng(7);st=time.time();acc=0
# mutate random relevant table or intercept; values bins 1.. perhaps 15
for it in range(6000):
 if rng.random()<.03: idx=1
 else:
  j=rng.integers(m+1); val=rng.integers(1, min(cap,12)+1);idx=2+j*(cap+1)+val
 delta=rng.choice(np.array([-.75,-.5,.5,.75]))
 t[idx]+=delta;c=obj(t)
 if c<=best: best=c;acc+=1
 else:t[idx]-=delta
 if it%1000==999:print(it+1,best,acc)
print('sec',time.time()-st)
de=sample_demands(s,128,5200,98765);out=evaluate(s,de,tabpol,t,200)
print('test',out[0].mean(),out[1].mean(0))
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "start 154.1412353515625 [11.832909061700018, 0.9912547214729119, 0.0954074559781346, 0.3650283239918575, 0.6323002192979327, 0.5507113526614439, 0.7232171161148501]\n1000 154.0863037109375 247\n2000 154.083251953125 450\n3000 154.08248901367188 643\n4000 154.08248901367188 828\n5000 154.08248901367188 1013\n6000 154.08248901367188 1207\nsec 83.34931516647339\ntest 154.41953125 [0.47956094 1.06463437 3.42136094]\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 100.7532927498687,
  "timed_out": false,
  "remaining_calls": 44,
  "remaining_seconds": 3139.7951875843573
}
````

## 工具调用 7

来自第 7 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np
# recorder linear Python
m=5;cv=1.5;f=.5
pa=dict(name='x',m=m,L=2,cv=cv,f=f,mean=4,h=0,p=100,w=100,demand_mode='paper_cv',cap_mode='paper');s=scenario_from_params(pa);cap=inventory_cap(s)
th=np.array([10.077,.668,.147,.252,.605,.378,.652])
from collections import Counter
cnt=Counter()
def rec(age,pipe):
 cnt[tuple(age)+(int(pipe[0]),)]+=1
 return th[0]-th[1]*pipe[0]-np.dot(th[2:],age)
d=sample_demands(s,64,2200,442)
out=evaluate_python(s,d,rec,200)
print(len(cnt),cnt.most_common(10), 'coverage top',[(n,sum(v for _,v in cnt.most_common(n))/sum(cnt.values())) for n in [100,500,1000,5000,10000]])
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "9300 [((np.int64(0), np.int64(0), np.int64(0), np.int64(0), np.int64(4), 5), 1706), ((np.int64(0), np.int64(0), np.int64(0), np.int64(0), np.int64(3), 3), 1651), ((np.int64(0), np.int64(0), np.int64(0), np.int64(0), np.int64(4), 3), 1587), ((np.int64(0), np.int64(0), np.int64(0), np.int64(0), np.int64(4), 4), 1495), ((np.int64(0), np.int64(0), np.int64(0), np.int64(0), np.int64(3), 4), 1438), ((np.int64(0), np.int64(0), np.int64(0), np.int64(0), np.int64(3), 5), 1436), ((np.int64(0), np.int64(0), np.int64(0), np.int64(0), np.int64(5), 4), 1416), ((np.int64(0), np.int64(0), np.int64(0), np.int64(0), np.int64(5), 3), 1201), ((np.int64(0), np.int64(0), np.int64(0), np.int64(0), np.int64(3), 6), 1060), ((np.int64(0), np.int64(0), np.int64(0), np.int64(0), np.int64(5), 5), 962)] coverage top [(100, 0.31443892045454547), (500, 0.5329758522727273), (1000, 0.6606036931818182), (5000, 0.9520738636363636), (10000, 1.0)]\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 3.837110875174403,
  "timed_out": false,
  "remaining_calls": 43,
  "remaining_seconds": 3135.958076709183
}
````

## 工具调用 8

来自第 8 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np,time
from collections import Counter
@njit
def rollout_actions(states, dem, th, cap, p, w, h):
 N=states.shape[0];K=dem.shape[0];H=dem.shape[1];m=states.shape[1]-1
 acts=np.zeros(N,np.int64); gaps=np.zeros(N)
 for n in range(N):
  room=cap
  for j in range(m+1): room-=states[n,j]
  best=1e100; besta=0; second=1e100
  for a in range(room+1):
   tot=0.
   for k in range(K):
    age=np.empty(m,np.int64)
    for j in range(m):age[j]=states[n,j]
    pipe=states[n,m]
    for tt in range(H):
     if tt==0:q=a
     else:
      raw=th[0]-th[1]*pipe
      for j in range(m):raw-=th[j+2]*age[j]
      rr=cap-pipe
      for j in range(m):rr-=age[j]
      if raw<0:raw=0.
      if raw>rr:raw=rr
      q=int(np.rint(raw))
     df=dem[k,tt,0]; dl=dem[k,tt,1]
     for j in range(m):
      z=min(df,age[j]);age[j]-=z;df-=z
     for jj in range(m):
      j=m-1-jj;z=min(dl,age[j]);age[j]-=z;dl-=z
     waste=age[0]; lost=df+dl
     surv=0
     for j in range(1,m):surv+=age[j]
     tot+=w*waste+p*lost+h*surv
     for j in range(m-1):age[j]=age[j+1]
     age[m-1]=pipe;pipe=q
   # end paths
   avg=tot/K
   if avg<best:
    second=best;best=avg;besta=a
   elif avg<second:second=avg
  acts[n]=besta; gaps[n]=second-best
 return acts,gaps

m=5;cv=1.5;f=.5
pa=dict(name='x',m=m,L=2,cv=cv,f=f,mean=4,h=0,p=100,w=100,demand_mode='paper_cv',cap_mode='paper');s=scenario_from_params(pa);cap=inventory_cap(s)
th=np.array([10.077,.668,.147,.252,.605,.378,.652])
cnt=Counter()
def rec(age,pipe):
 cnt[tuple(map(int,age))+(int(pipe[0]),)]+=1
 return th[0]-th[1]*pipe[0]-np.dot(th[2:],age)
evaluate_python(s,sample_demands(s,64,2200,442),rec,200)
states=np.array([x for x,c in cnt.most_common(5000)],dtype=np.int64)
droll=sample_demands(s,256,18,99173)
t=time.time();acts,gaps=rollout_actions(states,droll,th,cap,100.,100.,0.);print('roll sec',time.time()-t,'changed',np.mean(acts != [int(np.rint(max(0,min(cap-sum(st),th[0]-th[1]*st[-1]-np.dot(th[2:],st[:-1]))))) for st in states]),'gaps',np.quantile(gaps,[0,.5,.9,1]))
table={tuple(st):int(a) for st,a in zip(states,acts)}
def pol(age,pipe):
 key=tuple(map(int,age))+(int(pipe[0]),)
 if key in table:return table[key]
 return th[0]-th[1]*pipe[0]-np.dot(th[2:],age)
de=sample_demands(s,128,5200,98765);out=evaluate_python(s,de,pol,200)
print('test',out[0].mean(),out[1].mean(0),'states_eval overlap?')
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "roll sec 5.377973794937134 changed 0.5964 gaps [ 0.       2.34375  6.25    13.28125]\ntest 155.07453125 [0.53633438 1.01441094 3.52832188] states_eval overlap?\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 11.714263290865347,
  "timed_out": false,
  "remaining_calls": 42,
  "remaining_seconds": 3124.2438134183176
}
````

## 工具调用 9

来自第 9 次模型请求。

模型提交的代码：

````python
# Repeat compact by executing prior logic? fresh redefine via source abridged
from numba import njit
import numpy as np,time
from collections import Counter
@njit
def ro(states,dem,th,cap):
 N=states.shape[0];K=dem.shape[0];H=dem.shape[1];m=states.shape[1]-1;acts=np.zeros(N,np.int64); imp=np.zeros(N);basea=np.zeros(N,np.int64)
 for n in range(N):
  room=cap
  for j in range(m+1):room-=states[n,j]
  costs=np.zeros(room+1)
  raw=th[0]-th[1]*states[n,m]
  for j in range(m):raw-=th[j+2]*states[n,j]
  if raw<0:raw=0
  if raw>room:raw=room
  ba=int(np.rint(raw));basea[n]=ba
  for a in range(room+1):
   tot=0.
   for k in range(K):
    age=states[n,:m].copy();pipe=states[n,m]
    for tt in range(H):
     if tt==0:q=a
     else:
      raw=th[0]-th[1]*pipe
      rr=cap-pipe
      for j in range(m):raw-=th[j+2]*age[j];rr-=age[j]
      raw=max(0.,min(rr,raw));q=int(np.rint(raw))
     df=dem[k,tt,0];dl=dem[k,tt,1]
     for j in range(m):z=min(df,age[j]);age[j]-=z;df-=z
     for jj in range(m):j=m-1-jj;z=min(dl,age[j]);age[j]-=z;dl-=z
     tot+=100*(age[0]+df+dl)
     for j in range(m-1):age[j]=age[j+1]
     age[m-1]=pipe;pipe=q
   costs[a]=tot/K
  acts[n]=np.argmin(costs);imp[n]=costs[ba]-costs[acts[n]]
 return acts,imp,basea
m=5;s=Scenario('x',m,2,1.5,.5);cap=inventory_cap(s);th=np.array([10.077,.668,.147,.252,.605,.378,.652]);cnt=Counter()
def base(age,pipe):cnt[tuple(map(int,age))+(int(pipe[0]),)]+=1;return th[0]-th[1]*pipe[0]-np.dot(th[2:],age)
evaluate_python(s,sample_demands(s,64,2200,442),base,200);sts=np.array([x for x,c in cnt.most_common(5000)],np.int64)
for K in [256,1024]:
 a,imp,ba=ro(sts,sample_demands(s,K,20,99173),th,cap);print('K',K,'imp qs',np.quantile(imp,[0,.25,.5,.75,.9,.99,1]))
 de=sample_demands(s,128,5200,98765)
 for threshold in [0,2,4,6,8,10]:
  aa=np.where(imp>threshold,a,ba); tab={tuple(st):int(x) for st,x in zip(sts,aa)}
  def pol(age,pipe):
   key=tuple(map(int,age))+(int(pipe[0]),)
   return tab.get(key,th[0]-th[1]*pipe[0]-np.dot(th[2:],age))
  out=evaluate_python(s,de,pol,200)[0].mean();print(threshold,out,np.mean(aa!=ba))
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "K 256 imp qs [ 0.        0.390625  3.515625  7.421875 10.9375   16.40625  23.046875]\n0 155.7553125 0.7626\n2 155.46265625 0.6248\n4 155.08921875 0.4688\n6 154.79375 0.3292\n8 154.6746875 0.211\n10 154.51390625 0.1236\nK 1024 imp qs [0.         0.         0.         0.9765625  2.44140625 4.8828125\n 8.984375  ]\n0 154.393125 0.414\n2 154.24625 0.1336\n4 154.26640625 0.0256\n6 154.2946875 0.002\n8 154.29874999999998 0.0002\n10 154.29874999999998 0.0\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 98.45808595791459,
  "timed_out": false,
  "remaining_calls": 41,
  "remaining_seconds": 3025.785727460403
}
````

## 工具调用 10

来自第 10 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np
@njit
def lin(age,pipeline,th,mu,cv,f,L):
 z=th[0]-th[1]*pipeline[0]
 for i in range(age.size):z-=th[2+i]*age[i]
 return z
@njit
def bsp(age,pipeline,th,mu,cv,f,L): return th[0]-pipeline[0]-age.sum()
for m in [3,4,5]:
 for cv in [1.5,2]:
  for f in [0,.5]:
   s=Scenario('x',m,2,cv,f);cap=inventory_cap(s);d=sample_demands(s,32,2200,123)
   def ob(x):return evaluate(s,d,bsp,np.array(x),200)[0].mean()
   r=optimize(ob,[(0,cap)],[.6*cap],budget=64,seed=2)
   def ol(x):return evaluate(s,d,lin,np.array(x),200)[0].mean()
   rl=optimize(ol,[(0,cap)]+[(0,2)]*(m+1),np.r_[.6*cap,np.ones(m+1)],budget=1024,seed=2)
   de=sample_demands(s,64,5200,987)
   print(m,cv,f,'b',evaluate(s,de,bsp,r['theta'],200)[0].mean(),np.round(r['theta'],2),'lin',evaluate(s,de,lin,rl['theta'],200)[0].mean(),np.round(rl['theta'],2))
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "3 1.5 0 b 250.4346875 [11.23] lin 234.12562499999999 [8.93 1.29 1.92 0.04 1.56]\n3 1.5 0.5 b 222.38 [11.27] lin 204.0278125 [6.87 0.63 0.01 0.21 0.48]\n3 2 0 b 277.3578125 [8.59] lin 264.049375 [8.17 1.25 0.3  0.22 1.83]\n3 2 0.5 b 246.93312500000002 [9.86] lin 232.0103125 [5.94 0.65 0.2  0.13 0.48]\n4 1.5 0 b 215.5234375 [12.6] lin 203.30281250000002 [13.26  1.14  0.06  0.06  1.52  1.12]\n4 1.5 0.5 b 188.4953125 [14.09] lin 176.09625 [10.01  0.9   0.28  0.26  0.42  0.7 ]\n4 2 0 b 247.0228125 [10.8] lin 236.9665625 [11.44  1.18  0.03  0.    1.7   1.31]\n4 2 0.5 b 218.4115625 [11.23] lin 208.30281250000002 [7.67 0.77 0.11 0.32 0.28 0.68]\n5 1.5 0 b 189.66531250000003 [14.02] lin 178.79218749999998 [16.1   1.01  0.11  0.08  1.89  1.5   1.19]\n5 1.5 0.5 b 163.31062500000002 [14.72] lin 154.995 [13.39  1.08  0.12  0.37  0.63  0.69  0.93]\n5 2 0 b 224.92281250000002 [13.2] lin 215.00656250000003 [14.01  1.08  0.03  0.02  1.99  1.5   1.07]\n5 2 0.5 b 197.04 [12.6] lin 189.67843750000003 [9.24 0.91 0.06 0.3  0.67 0.51 0.52]\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 73.89575616689399,
  "timed_out": false,
  "remaining_calls": 40,
  "remaining_seconds": 2951.889971293509
}
````

## 工具调用 11

来自第 11 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np,time
@njit
def hinge(age,pipeline,th,mu,cv,f,L):
 m=age.size;z=th[0]-th[1]*pipeline[0]; T=0.;R=pipeline[0]
 for i in range(m):
  z-=th[2+i]*age[i];T+=age[i]
  if i>=2:R+=age[i]
 off=m+2
 z+=th[off]*max(0.,T-4)+th[off+1]*max(0.,T-8)+th[off+2]*max(0.,R-4)+th[off+3]*max(0.,R-8)
 return z
@njit
def lin(age,pipeline,th,mu,cv,f,L):
 z=th[0]-th[1]*pipeline[0]
 for i in range(age.size):z-=th[2+i]*age[i]
 return z
for m,cv,f in [(3,1.5,0),(3,1.5,.5),(5,1.5,0),(5,1.5,.5),(5,2,0),(5,2,.5)]:
 s=Scenario('x',m,2,cv,f);cap=inventory_cap(s);d=sample_demands(s,64,4200,12345)
 def obj(x):return evaluate(s,d,hinge,np.asarray(x),200)[0].mean()
 ini=np.r_[.6*cap,np.ones(m+1),np.zeros(4)]
 r=optimize(obj,[(0,cap)]+[(0,2)]*(m+1)+[(-1.5,1.5)]*4,ini,budget=3072,seed=22)
 de=sample_demands(s,128,5200,98765);o=evaluate(s,de,hinge,r['theta'],200)
 print((m,cv,f),'tr',r['cost'],'te',o[0].mean(),'th',np.round(r['theta'],2),'sec',r['seconds'])
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 1.5, 0) tr 234.292578125 te 233.34796875 th [ 9.45  0.84  1.23  0.19  1.33  0.98 -0.58 -0.52  0.7 ] sec 37.66141149983741\n(3, 1.5, 0.5) tr 201.529296875 te 203.91609375000002 th [7.79 0.65 0.64 0.69 0.78 0.57 0.14 0.15 0.24] sec 27.02113795792684\n(5, 1.5, 0) tr 178.5953125 te 178.0796875 th [16.42  0.41  0.23  0.25  1.61  1.22  1.    0.5   0.55 -1.16  0.25] sec 75.41654825001024\n(5, 1.5, 0.5) tr 151.717578125 te 154.27531249999998 th [12.09  0.91  0.59  0.79  1.16  1.1   1.18  0.65 -0.25  0.25 -0.16] sec 85.0507352501154\n(5, 2, 0) tr 214.9328125 te 217.29953125 th [14.4   0.53  0.18  0.45  1.85  1.27  0.85  0.65 -0.28 -0.96 -0.79] sec 84.84065716690384\n(5, 2, 0.5) tr 190.136328125 te 191.69171875 th [10.73  1.12  0.49  0.65  0.94  1.01  1.17  0.27  0.14  0.38 -0.17] sec 112.88406545901671\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 425.8254274588544,
  "timed_out": false,
  "remaining_calls": 39,
  "remaining_seconds": 2526.0645438346546
}
````

## 工具调用 12

来自第 12 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np,time
@njit
def lin(age,pipeline,th,mu,cv,f,L):
 z=th[0]-th[1]*pipeline[0]
 for i in range(age.size):z-=th[2+i]*age[i]
 return z
results={}
T=time.time()
for m in [3,4,5]:
 for cv in [1.5,2.0]:
  for f in [0.,.5]:
   s=Scenario('x',m,2,cv,f);cap=inventory_cap(s)
   # 128*6000 =768k
   d=sample_demands(s,128,6200,202503)
   def obj(x):return evaluate(s,d,lin,np.asarray(x),200)[0].mean()
   init=np.r_[.6*cap,np.r_[1,np.zeros(2),np.ones(max(0,m-2))]] # incorrect total m+1 yes
   r=optimize(obj,[(0,cap)]+[(0,2)]*(m+1),init,budget=2048,seed=100*m+int(10*cv)+int(f*2))
   de=sample_demands(s,128,10200,987654);o=evaluate(s,de,lin,r['theta'],200)
   results[(m,cv,f)]=(r['theta'],o[0].mean())
   print((m,cv,f),'train',round(r['cost'],4),'test',round(o[0].mean(),4),'se',round(o[0].std()/np.sqrt(128),3),'comp',np.round(o[1].mean(0),4),'th',np.round(r['theta'],4),'sec',round(r['seconds'],1),flush=True)
print('TOTAL',time.time()-T)
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 1.5, 0.0) train 233.7914 test 233.5998 se 0.365 comp [0.6703 1.6657 3.    ] th [8.8886 0.9674 0.1547 0.0522 0.8753] sec 73.5\n(3, 1.5, 0.5) train 204.1125 test 204.6703 se 0.476 comp [0.5181 1.5286 3.    ] th [9.5734 1.1715 0.0209 0.2596 0.8797] sec 15.1\n(3, 2.0, 0.0) train 262.5385 test 264.0252 se 0.57 comp [0.6507 1.9896 2.6667] th [8.696  1.0614 0.1466 0.0509 1.1259] sec 59.9\n(3, 2.0, 0.5) train 233.0281 test 234.2735 se 0.55 comp [0.484  1.8587 2.6293] th [6.1629 0.7231 0.062  0.265  0.4761] sec 43.2\n(4, 1.5, 0.0) train 203.2411 test 203.3259 se 0.344 comp [0.6183 1.415  3.1987] th [1.19152e+01 9.89500e-01 1.22000e-02 3.00000e-03 1.39780e+00 1.03730e+00] sec 136.3\n(4, 1.5, 0.5) train 175.7688 test 176.2602 se 0.43 comp [0.5362 1.2264 3.3203] th [7.7233 0.515  0.1029 0.2478 0.2918 0.5336] sec 131.5\n(4, 2.0, 0.0) train 236.0893 test 237.6251 se 0.559 comp [0.5527 1.8235 2.7347] th [11.2608  1.1088  0.1289  0.1269  1.4504  1.1758] sec 161.2\n(4, 2.0, 0.5) train 209.1497 test 210.3949 se 0.534 comp [0.456 1.648 2.812] th [7.4797 0.7652 0.0891 0.2826 0.4185 0.5222] sec 183.9\n(5, 1.5, 0.0) train 178.4409 test 178.3546 se 0.338 comp [0.5553 1.2283 3.3224] th [15.4063  1.0242  0.0347  0.0631  1.8177  1.4152  1.1103] sec 177.8\n(5, 1.5, 0.5) train 153.9868 test 154.3506 se 0.404 comp [0.4914 1.0521 3.4498] th [9.7485 0.6727 0.2093 0.1971 0.4761 0.5081 0.5266] sec 179.5\n(5, 2.0, 0.0) train 214.1336 test 215.7464 se 0.536 comp [0.5412 1.6163 2.9304] th [1.43697e+01 1.13930e+00 1.46000e-02 1.41000e-02 1.88220e+00 1.62290e+00\n 1.23430e+00] sec 116.8\n(5, 2.0, 0.5) train 190.7745 test 191.8052 se 0.528 comp [0.4055 1.5126 2.8969] th [8.8721 0.8445 0.1662 0.3087 0.4041 0.4648 0.6294] sec 163.8\nTOTAL 1450.6559331417084\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 1451.7574765419122,
  "timed_out": false,
  "remaining_calls": 38,
  "remaining_seconds": 1074.3070672927424
}
````

## 工具调用 13

来自第 13 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np,time
@njit
def lin(age,pipeline,th,mu,cv,f,L):
 z=th[0]-th[1]*pipeline[0]
 for i in range(age.size):z-=th[2+i]*age[i]
 return z
C={
(3,1.5,0):[[8.699,1.442,1.481,.001,1.188],[8.8886,.9674,.1547,.0522,.8753]],
(3,1.5,.5):[[7.28,.76,.161,.132,.451],[9.5734,1.1715,.0209,.2596,.8797]],
(3,2.,0):[[8.17,1.25,.3,.22,1.83],[8.696,1.0614,.1466,.0509,1.1259]],
(3,2.,.5):[[5.94,.65,.2,.13,.48],[6.1629,.7231,.062,.265,.4761]],
(4,1.5,0):[[13.26,1.14,.06,.06,1.52,1.12],[11.9152,.9895,.0122,.003,1.3978,1.0373]],
(4,1.5,.5):[[10.01,.9,.28,.26,.42,.7],[7.7233,.515,.1029,.2478,.2918,.5336]],
(4,2.,0):[[11.44,1.18,.03,0,1.7,1.31],[11.2608,1.1088,.1289,.1269,1.4504,1.1758]],
(4,2.,.5):[[7.67,.77,.11,.32,.28,.68],[7.4797,.7652,.0891,.2826,.4185,.5222]],
(5,1.5,0):[[16.1,1.01,.11,.08,1.89,1.5,1.19],[15.4063,1.0242,.0347,.0631,1.8177,1.4152,1.1103]],
(5,1.5,.5):[[10.077,.668,.147,.252,.605,.378,.652],[9.7485,.6727,.2093,.1971,.4761,.5081,.5266]],
(5,2.,0):[[14.01,1.08,.03,.02,1.99,1.5,1.07],[14.3697,1.1393,.0146,.0141,1.8822,1.6229,1.2343]],
(5,2.,.5):[[9.24,.91,.06,.3,.67,.51,.52],[8.8721,.8445,.1662,.3087,.4041,.4648,.6294]]}
for key,cs in C.items():
 m,cv,f=key;s=Scenario('x',m,2,cv,f);d=sample_demands(s,256,20200,314159)
 vals=[]
 for th in cs:
  o=evaluate(s,d,lin,np.array(th),200);vals.append((o[0].mean(),o[1].mean(0)))
 print(key,[(round(x,4),np.round(y,4)) for x,y in vals])
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 1.5, 0) [(np.float64(234.185), array([0.6388, 1.703 , 2.935 ])), (np.float64(233.7273), array([0.6691, 1.6682, 3.    ]))]\n(3, 1.5, 0.5) [(np.float64(203.5167), array([0.5851, 1.4501, 3.1339])), (np.float64(203.9476), array([0.5203, 1.5192, 3.    ]))]\n(3, 2.0, 0) [(np.float64(265.107), array([0.5211, 2.1299, 2.397 ])), (np.float64(264.1092), array([0.651 , 1.9901, 2.6667]))]\n(3, 2.0, 0.5) [(np.float64(234.2324), array([0.4896, 1.8527, 2.6366])), (np.float64(234.1853), array([0.4856, 1.8562, 2.629 ]))]\n(4, 1.5, 0) [(np.float64(203.2654), array([0.647 , 1.3856, 3.2605])), (np.float64(203.2747), array([0.6159, 1.4169, 3.198 ]))]\n(4, 1.5, 0.5) [(np.float64(175.7343), array([0.5373, 1.22  , 3.3162])), (np.float64(175.6251), array([0.5386, 1.2177, 3.3198]))]\n(4, 2.0, 0) [(np.float64(237.6924), array([0.5451, 1.8318, 2.719 ])), (np.float64(237.6024), array([0.5524, 1.8236, 2.7345]))]\n(4, 2.0, 0.5) [(np.float64(210.5402), array([0.436 , 1.6694, 2.7663])), (np.float64(210.3081), array([0.4573, 1.6457, 2.8112]))]\n(5, 1.5, 0) [(np.float64(178.6002), array([0.5931, 1.1929, 3.3992])), (np.float64(178.4909), array([0.555 , 1.2299, 3.3242]))]\n(5, 1.5, 0.5) [(np.float64(153.9502), array([0.4875, 1.052 , 3.4343])), (np.float64(153.8037), array([0.4939, 1.0441, 3.4486]))]\n(5, 2.0, 0) [(np.float64(215.8232), array([0.5579, 1.6004, 2.9632])), (np.float64(215.6708), array([0.5406, 1.6161, 2.9303]))]\n(5, 2.0, 0.5) [(np.float64(191.7909), array([0.4269, 1.491 , 2.9355])), (np.float64(191.7564), array([0.4068, 1.5107, 2.8957]))]\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 23.640020749997348,
  "timed_out": false,
  "remaining_calls": 37,
  "remaining_seconds": 1050.667046542745
}
````

## 工具调用 14

来自第 14 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np,time
@njit
def lin(age,pipeline,th,mu,cv,f,L):
 z=th[0]-th[1]*pipeline[0]
 for i in range(age.size):z-=th[2+i]*age[i]
 return z
B={
(3,1.5,0):[8.8886,.9674,.1547,.0522,.8753],(3,1.5,.5):[7.28,.76,.161,.132,.451],
(3,2.,0):[8.696,1.0614,.1466,.0509,1.1259],(3,2.,.5):[6.1629,.7231,.062,.265,.4761],
(4,1.5,0):[13.26,1.14,.06,.06,1.52,1.12],(4,1.5,.5):[7.7233,.515,.1029,.2478,.2918,.5336],
(4,2.,0):[11.2608,1.1088,.1289,.1269,1.4504,1.1758],(4,2.,.5):[7.4797,.7652,.0891,.2826,.4185,.5222],
(5,1.5,0):[15.4063,1.0242,.0347,.0631,1.8177,1.4152,1.1103],(5,1.5,.5):[9.7485,.6727,.2093,.1971,.4761,.5081,.5266],
(5,2.,0):[14.3697,1.1393,.0146,.0141,1.8822,1.6229,1.2343],(5,2.,.5):[8.8721,.8445,.1662,.3087,.4041,.4648,.6294]}
OUT={}
for key,b in B.items():
 m,cv,f=key;s=Scenario('x',m,2,cv,f);d=sample_demands(s,128,10200,271828)
 b=np.array(b);best=(1e9,None)
 for ds in np.linspace(-1,1,9):
  for lam in np.linspace(.8,1.2,9):
   x=b.copy();x[0]+=ds;x[1:]*=lam
   c=evaluate(s,d,lin,x,200)[0].mean()
   if c<best[0]:best=(c,x.copy())
 # validation same huge used prior different seed
 dv=sample_demands(s,256,20200,314159)
 cb=evaluate(s,dv,lin,b,200)[0].mean();cn=evaluate(s,dv,lin,best[1],200)[0].mean()
 OUT[key]=best[1]
 print(key,'trainbest',round(best[0],4),'baseval',round(cb,4),'newval',round(cn,4),'x',np.round(best[1],4),flush=True)
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 1.5, 0) trainbest 234.0427 baseval 233.7273 newval 233.7444 x [7.8886 0.7739 0.1238 0.0418 0.7002]\n(3, 1.5, 0.5) trainbest 202.8729 baseval 203.5167 newval 203.4888 x [7.03   0.722  0.153  0.1254 0.4284]\n(3, 2.0, 0) trainbest 263.7534 baseval 264.1092 newval 264.1092 x [8.696  1.0614 0.1466 0.0509 1.1259]\n(3, 2.0, 0.5) trainbest 234.0068 baseval 234.1853 newval 234.1662 x [5.6629 0.6146 0.0527 0.2253 0.4047]\n(4, 1.5, 0) trainbest 203.4852 baseval 203.2654 newval 203.3096 x [13.01   1.083  0.057  0.057  1.444  1.064]\n(4, 1.5, 0.5) trainbest 175.1309 baseval 175.6251 newval 175.6368 x [8.2233 0.5665 0.1132 0.2726 0.321  0.587 ]\n(4, 2.0, 0) trainbest 237.3491 baseval 237.6024 newval 237.6807 x [10.7608  1.0534  0.1225  0.1206  1.3779  1.117 ]\n(4, 2.0, 0.5) trainbest 210.0232 baseval 210.3081 newval 210.3028 x [6.9797 0.6887 0.0802 0.2543 0.3766 0.47  ]\n(5, 1.5, 0) trainbest 178.7099 baseval 178.4909 newval 178.4909 x [15.4063  1.0242  0.0347  0.0631  1.8177  1.4152  1.1103]\n(5, 1.5, 0.5) trainbest 153.3056 baseval 153.8037 newval 153.8104 x [8.9985 0.6054 0.1884 0.1774 0.4285 0.4573 0.4739]\n(5, 2.0, 0) trainbest 215.1984 baseval 215.6708 newval 215.5794 x [1.33697e+01 1.02540e+00 1.31000e-02 1.27000e-02 1.69400e+00 1.46060e+00\n 1.11090e+00]\n(5, 2.0, 0.5) trainbest 191.4014 baseval 191.7564 newval 191.7564 x [8.8721 0.8445 0.1662 0.3087 0.4041 0.4648 0.6294]\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 173.6113694589585,
  "timed_out": false,
  "remaining_calls": 36,
  "remaining_seconds": 877.0556770837866
}
````

## 工具调用 15

来自第 15 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np
@njit
def lin(age,pipeline,th,mu,cv,f,L):
 z=th[0]-th[1]*pipeline[0]
 for i in range(age.size):z-=th[2+i]*age[i]
 return z
B={(3,1.5):[8.8886,.9674,.1547,.0522,.8753],(3,2.):[8.696,1.0614,.1466,.0509,1.1259],(4,1.5):[13.26,1.14,.06,.06,1.52,1.12],(4,2.):[11.2608,1.1088,.1289,.1269,1.4504,1.1758],(5,1.5):[15.4063,1.0242,.0347,.0631,1.8177,1.4152,1.1103],(5,2.):[14.3697,1.1393,.0146,.0141,1.8822,1.6229,1.2343]}
for (m,cv),b in B.items():
 s=Scenario('x',m,2,cv,0);d=sample_demands(s,256,20200,314159);b=np.array(b);x=b.copy();x[2:4]=0
 o=[]
 for z in [b,x]:o.append(evaluate(s,d,lin,z,200)[0].mean())
 print(m,cv,o,'delta',o[1]-o[0])
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "3 1.5 [np.float64(233.72728515625), np.float64(233.714921875)] delta -0.01236328125000341\n3 2.0 [np.float64(264.10919921875), np.float64(264.13648437499995)] delta 0.02728515624994543\n4 1.5 [np.float64(203.26544921875), np.float64(203.17263671875)] delta -0.09281250000000796\n4 2.0 [np.float64(237.60236328124998), np.float64(237.4758203125)] delta -0.1265429687499875\n5 1.5 [np.float64(178.4908984375), np.float64(178.45005859375)] delta -0.04083984375000682\n5 2.0 [np.float64(215.67083984375), np.float64(215.671328125)] delta 0.00048828125\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 21.19416020787321,
  "timed_out": false,
  "remaining_calls": 35,
  "remaining_seconds": 855.8615168759134
}
````

## 工具调用 16

来自第 16 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np,time
@njit
def p0(age,pipeline,th,mu,cv,f,L):
 z=th[0]-th[1]*pipeline[0]
 for i in range(2,age.size):z-=th[i]*age[i] # theta i maps age index i, length m
 return z
BASE={(3,1.5):[8.8886,.9674,.8753],(3,2.):[8.696,1.0614,1.1259],(4,1.5):[13.26,1.14,1.52,1.12],(4,2.):[11.2608,1.1088,1.4504,1.1758],(5,1.5):[15.4063,1.0242,1.8177,1.4152,1.1103],(5,2.):[14.3697,1.1393,1.8822,1.6229,1.2343]}
for (m,cv),ini in BASE.items():
 s=Scenario('x',m,2,cv,0);cap=inventory_cap(s);d=sample_demands(s,96,6200,424242)
 def obj(x):return evaluate(s,d,p0,np.asarray(x),200)[0].mean()
 r=optimize(obj,[(0,cap)]+[(0,2)]*(m-1),ini,budget=1536,seed=m*10+int(cv*2))
 dv=sample_demands(s,256,20200,314159)
 old=evaluate(s,dv,p0,np.array(ini),200)[0].mean();new=evaluate(s,dv,p0,r['theta'],200)[0].mean()
 print((m,cv),'tr',r['cost'],'val old/new',old,new,'th',np.round(r['theta'],4),'sec',r['seconds'],flush=True)
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 1.5) tr 233.72638888888892 val old/new 233.714921875 233.73337890625 th [9.6251 1.1357 1.0164] sec 66.30092508299276\n(3, 2.0) tr 264.32673611111113 val old/new 264.13648437499995 264.13382812500004 th [7.2107 0.5675 1.0656] sec 38.12313770898618\n(4, 1.5) tr 203.48038194444447 val old/new 203.17263671875 203.18857421875 th [13.4035  1.1492  1.5029  1.1291] sec 60.72769754100591\n(4, 2.0) tr 237.5564236111111 val old/new 237.4758203125 237.45990234375 th [11.3296  1.1534  1.4565  1.1897] sec 49.439298999961466\n(5, 1.5) tr 178.1394097222222 val old/new 178.45005859375 178.45513671875 th [15.2035  1.0122  1.703   1.3787  1.13  ] sec 114.672846917063\n(5, 2.0) tr 215.69149305555553 val old/new 215.671328125 215.66732421875 th [14.3292  1.1192  1.8733  1.5679  1.1964] sec 78.3116256671492\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 427.874626792036,
  "timed_out": false,
  "remaining_calls": 34,
  "remaining_seconds": 427.98689008387737
}
````

## 工具调用 17

来自第 17 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np
@njit
def p0(age,pipeline,th,mu,cv,f,L):
 z=th[0]-th[1]*pipeline[0]
 for i in range(2,age.size):z-=th[i]*age[i]
 return z
D={(3,1.5):([8.8886,.9674,.8753],[9.6251,1.1357,1.0164]),(3,2.):([8.696,1.0614,1.1259],[7.2107,.5675,1.0656]),(4,1.5):([13.26,1.14,1.52,1.12],[13.4035,1.1492,1.5029,1.1291]),(4,2.):([11.2608,1.1088,1.4504,1.1758],[11.3296,1.1534,1.4565,1.1897]),(5,1.5):([15.4063,1.0242,1.8177,1.4152,1.1103],[15.2035,1.0122,1.703,1.3787,1.13]),(5,2.):([14.3697,1.1393,1.8822,1.6229,1.2343],[14.3292,1.1192,1.8733,1.5679,1.1964])}
for key,(a,b) in D.items():
 s=Scenario('x',key[0],2,key[1],0);d=sample_demands(s,256,20200,161803)
 print(key,[evaluate(s,d,p0,np.array(x),200)[0].mean() for x in [a,b]])
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 1.5) [np.float64(234.03384765625), np.float64(234.04636718749998)]\n(3, 2.0) [np.float64(263.7568359375), np.float64(263.7698046875)]\n(4, 1.5) [np.float64(203.3994140625), np.float64(203.40875)]\n(4, 2.0) [np.float64(237.17628906250002), np.float64(237.17677734375)]\n(5, 1.5) [np.float64(178.67335937500002), np.float64(178.71833984375002)]\n(5, 2.0) [np.float64(215.32621093749998), np.float64(215.33060546874998)]\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 19.349598624976352,
  "timed_out": false,
  "remaining_calls": 33,
  "remaining_seconds": 408.637291458901
}
````

## 工具调用 18

来自第 18 次模型请求。

模型提交的代码：

````python
from numba import njit
import numpy as np
@njit
def lin(age,pipeline,th,mu,cv,f,L):
 z=th[0]-th[1]*pipeline[0]
 for i in range(age.size):z-=th[2+i]*age[i]
 return z
D={(3,1.5):([7.28,.76,.161,.132,.451],[7.03,.722,.153,.1254,.4284]),(3,2.):([6.1629,.7231,.062,.265,.4761],[5.6629,.6146,.0527,.2253,.4047]),(4,1.5):([7.7233,.515,.1029,.2478,.2918,.5336],[8.2233,.5665,.1132,.2726,.321,.587]),(4,2.):([7.4797,.7652,.0891,.2826,.4185,.5222],[6.9797,.6887,.0802,.2543,.3766,.47]),(5,1.5):([9.7485,.6727,.2093,.1971,.4761,.5081,.5266],[8.9985,.6054,.1884,.1774,.4285,.4573,.4739]),(5,2.):([8.8721,.8445,.1662,.3087,.4041,.4648,.6294],[8.8721,.8445,.1662,.3087,.4041,.4648,.6294])}
for key,(a,b) in D.items():
 s=Scenario('x',key[0],2,key[1],.5);d=sample_demands(s,256,20200,161803)
 print(key,[evaluate(s,d,lin,np.array(x),200)[0].mean() for x in [a,b]])
````

系统实际返回给模型的反馈：

````json
{
  "stdout": "(3, 1.5) [np.float64(203.76037109375), np.float64(203.730234375)]\n(3, 2.0) [np.float64(235.19005859375), np.float64(235.17201171875)]\n(4, 1.5) [np.float64(175.79003906249997), np.float64(175.79986328125)]\n(4, 2.0) [np.float64(211.2595703125), np.float64(211.265234375)]\n(5, 1.5) [np.float64(153.96652343749997), np.float64(153.96626953125)]\n(5, 2.0) [np.float64(192.66033203125), np.float64(192.66033203125)]\n",
  "stderr": "",
  "returncode": 0,
  "elapsed_seconds": 23.938053415855393,
  "timed_out": false,
  "remaining_calls": 32,
  "remaining_seconds": 384.6992380430456
}
````
