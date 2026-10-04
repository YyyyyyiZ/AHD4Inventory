import numpy as np,time
from scipy.optimize import differential_evolution
from scipy.special import ndtr
rng=np.random.default_rng(6677);N=30000;D=rng.poisson(100,(N,50)).astype(np.float32);rt=np.sqrt(2*np.pi);init=np.array([101,96,96,96,95,96.])
def obj(v):
 U,no=v[:2];coef=v[2:];x=np.full(N,init[0]);p=np.tile(init[1:,None],(1,N));c=0
 for t in range(50):
  m=x.copy();vv=np.zeros(N); adj=np.zeros(N)
  for k in range(6):
   mu=m-100;sd=np.sqrt(vv+no);aa=mu/sd;P=ndtr(aa);f=np.exp(-aa*aa/2)/rt
   mm=sd*f+mu*P;s=(sd*sd+mu*mu)*P+mu*sd*f
   vv=np.maximum(0,s-mm*mm);m=mm
   adj += coef[k]*m
   if k<5:m+=p[k]
  q=np.clip(U-adj,0,U)
  d=D[:,t];z=np.minimum(x,d);x-=z;c+=(x+2*(d-z)).sum();x+=p[0];p[:-1]=p[1:];p[-1]=q
 return c/N
bounds=[(94,104),(20,150)]+[(-.5,1.5)]*6
res=differential_evolution(obj,bounds,popsize=7,maxiter=30,tol=.0015,polish=True,seed=7,disp=True)
print(res.fun,res.x)