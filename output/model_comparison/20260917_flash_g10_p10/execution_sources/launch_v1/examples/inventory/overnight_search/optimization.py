"""Identical derivative-free parameter optimizer used across all structure arms."""
import time
import numpy as np
from scipy.optimize import differential_evolution
from scipy.stats import qmc


def optimize(objective, bounds, initial, budget=256, seed=1):
    bounds = np.asarray(bounds, dtype=float)
    initial = np.asarray(initial, dtype=float)
    start = time.monotonic()
    nfev, best, best_x = 0, float('inf'), initial.copy()
    class Done(Exception):
        pass
    def fun(x):
        nonlocal nfev, best, best_x
        if nfev >= budget:
            raise Done()
        nfev += 1
        val = float(objective(x))
        if not np.isfinite(val):
            raise ValueError("Nonfinite simulation objective")
        if val < best:
            best, best_x = val, np.asarray(x).copy()
        return val
    fun(initial)
    if len(initial):
        pop = qmc.LatinHypercube(d=len(initial), seed=seed).random(16)
        pop = qmc.scale(pop, bounds[:, 0], bounds[:, 1])
        pop[0] = initial
        try:
            differential_evolution(fun, bounds, init=pop, maxiter=budget,
                                   mutation=(.4, 1.), recombination=.8,
                                   rng=seed, polish=False, tol=0., atol=0.)
        except Done:
            pass
    return {"theta": best_x.tolist(), "cost": best, "nfev": nfev,
            "seconds": time.monotonic()-start}
