import numpy as np
from scipy.optimize import minimize
rng=np.random.default_rng(8888);N=220000;T=50
D=np.rint(np.maximum(0,rng.normal(100,30,(N,T)))).astype(np.float32)
a=np.array([103.28,89.555,88.264,86.951,87.483,86.5])
def sim(x,detail=False):
 R,k=x[:2];ds=x[2:];I=np.zeros(N);pipe=np.tile(a,(N,1));c=np.zeros(N)
 for t in range(T):
  I+=pipe[:,0];pipe[:,:-1]=pipe[:,1:];pipe[:,-1]=0
  y=np.maximum(I-ds[0],0)
  for j in range(5):y=np.maximum(y+pipe[:,j]-ds[j+1],0)
  pipe[:,-1]=np.maximum(0,R-k*y)
  s=np.minimum(I,D[:,t]);I-=s;c+=I+2*(D[:,t]-s)
 return c.mean()
x0=np.array([87.999,.349276,75.6943,93.333,98.7288,98.7501,98.75,98.75])
print('start',sim(x0))
res=minimize(sim,x0,method='Powell',bounds=[(82,94),(.05,1.5)]+[(50,120)]*6,options={'maxiter':12,'xtol':.015,'ftol':2e-8,'disp':True})
print(res.fun,res.x,sim(res.x))