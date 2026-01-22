"""
Parametric Stochastic Dynamic Programming (DP) baseline for Inventory Control with Lead Time L=2.

This script:
1) Loads the three training JSON files:
   - exponential_L2_c1_2_train.json
   - normal_L2_c1_2_train.json
   - poisson_L2_c1_2_train.json
2) Solves an approximate finite-horizon stochastic DP on a coarse grid using the *parametric* demand model
   (not the realized trajectories).
3) Evaluates the learned policy on every trajectory in each file and reports average realized cost.

Important notes:
- Lead time is assumed to be L=2 (consistent with the file names).
- The DP uses a coarse grid (default: 10 units) for tractability. Orders are multiples of grid_step.
- Demand is modeled as nonnegative integer:
  * exponential: D = round(Exp(mean=100))
  * normal:      D = max(0, round(N(mean=100, std=std_normal)))
  * poisson:     D ~ Poisson(lambda=100)
- First L periods have zero demand in the provided trajectories. We also do not charge cost in those periods.

All printed output is in English.
"""
from __future__ import annotations

import json
import math
import os
import statistics
import time
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


# ----------------------------
# Utility: Normal CDF
# ----------------------------
def norm_cdf(z: float) -> float:
    """Standard normal CDF using erf."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# ----------------------------
# Demand models (integer, nonnegative)
# ----------------------------
class DiscreteDemandModel:
    def pmf(self, k: int) -> float:
        raise NotImplementedError

    def cdf(self, k: int) -> float:
        raise NotImplementedError

    def mean(self) -> float:
        raise NotImplementedError


class ExponentialRoundedDemand(DiscreteDemandModel):
    """
    Demand D = round(X) where X ~ Exp(scale=mu).
    Then:
      P(D=0) = 1 - exp(-0.5/mu)
      P(D=k) = exp(-(k-0.5)/mu) - exp(-(k+0.5)/mu), k>=1
      CDF(k) = P(D<=k) = 1 - exp(-(k+0.5)/mu), k>=0
    """
    def __init__(self, mu: float):
        self.mu = float(mu)
        self._r = math.exp(-1.0 / self.mu)       # r = exp(-1/mu)
        self._sqrt_r = math.exp(-0.5 / self.mu)  # exp(-0.5/mu)

    def pmf(self, k: int) -> float:
        if k < 0:
            return 0.0
        if k == 0:
            return 1.0 - self._sqrt_r
        # (1-r)*r^{k-0.5} = (1-r)*sqrt_r*r^{k-1}
        return (1.0 - self._r) * self._sqrt_r * (self._r ** (k - 1))

    def cdf(self, k: int) -> float:
        if k < 0:
            return 0.0
        # 1 - exp(-(k+0.5)/mu) = 1 - sqrt_r*r^k
        return 1.0 - self._sqrt_r * (self._r ** k)

    def mean(self) -> float:
        # E[D] = sqrt(r)/(1-r)
        return self._sqrt_r / (1.0 - self._r)


class NormalRoundedTruncatedDemand(DiscreteDemandModel):
    """
    Demand D = max(0, round(X)), X ~ N(mu, sigma).
    Then:
      CDF(k)=P(D<=k)=Phi((k+0.5-mu)/sigma), k>=0
      PMF(0)=CDF(0)
      PMF(k)=CDF(k)-CDF(k-1), k>=1
    """
    def __init__(self, mu: float, sigma: float):
        self.mu = float(mu)
        self.sigma = float(sigma)

    def cdf(self, k: int) -> float:
        if k < 0:
            return 0.0
        z = (k + 0.5 - self.mu) / self.sigma
        return norm_cdf(z)

    def pmf(self, k: int) -> float:
        if k < 0:
            return 0.0
        if k == 0:
            return self.cdf(0)
        return max(0.0, self.cdf(k) - self.cdf(k - 1))

    def mean(self) -> float:
        # True mean differs slightly due to rounding/clipping; we estimate it in the cost precompute.
        return self.mu


class PoissonDemand(DiscreteDemandModel):
    """Poisson demand with precomputed pmf/cdf tables for speed."""
    def __init__(self, lam: float, k_max_for_tables: int = 5000):
        self.lam = float(lam)
        self.k_max = int(k_max_for_tables)

        pmf = np.zeros(self.k_max + 1, dtype=float)
        pmf[0] = math.exp(-self.lam)
        for k in range(0, self.k_max):
            pmf[k + 1] = pmf[k] * self.lam / (k + 1)

        self._pmf_arr = pmf
        self._cdf_arr = np.cumsum(pmf)

    def pmf(self, k: int) -> float:
        if k < 0:
            return 0.0
        if k <= self.k_max:
            return float(self._pmf_arr[k])
        return 0.0  # tail is negligible for our usage

    def cdf(self, k: int) -> float:
        if k < 0:
            return 0.0
        if k >= self.k_max:
            return 1.0
        return float(self._cdf_arr[k])

    def mean(self) -> float:
        return self.lam


# ----------------------------
# DP config and helpers
# ----------------------------
@dataclass
class DPConfigL2:
    step: int
    x_max: int
    y_max: int
    Nx: int
    Ny: int
    lead_time: int
    horizon: int


def ceil_to_step(v: float, step: int) -> int:
    return int(math.ceil(v / step) * step)


def build_model_from_instance(instance: dict) -> DiscreteDemandModel:
    dist = str(instance.get("distribution", "")).lower()
    mu = 100.0  # per your problem statement (and consistent with the datasets)
    if dist == "exponential":
        return ExponentialRoundedDemand(mu)
    if dist == "poisson":
        return PoissonDemand(mu, k_max_for_tables=5000)
    if dist == "normal":
        sigma = instance.get("std_normal", 30.0) or 30.0
        return NormalRoundedTruncatedDemand(mu, float(sigma))
    raise ValueError(f"Unsupported distribution: {dist}")


def estimate_std_for_bounds(model: DiscreteDemandModel) -> float:
    if isinstance(model, ExponentialRoundedDemand):
        return model.mu
    if isinstance(model, PoissonDemand):
        return math.sqrt(model.lam)
    if isinstance(model, NormalRoundedTruncatedDemand):
        return model.sigma
    return 100.0


def precompute_immediate_costs(
    model: DiscreteDemandModel,
    holding_cost: float,
    lost_sales_cost: float,
    x_max: int,
) -> np.ndarray:
    """
    Expected one-period cost as a function of on-hand inventory x (integer):
        E[h*(x-D)+ + p*(D-x)+]
    Computed using prefix sums on a large demand support (tail is negligible at our cutoff).
    """
    h = float(holding_cost)
    p = float(lost_sales_cost)

    # Large support to make tail negligible (especially important for exponential).
    if isinstance(model, ExponentialRoundedDemand):
        k_support = max(5000, x_max + 2000)
    elif isinstance(model, PoissonDemand):
        k_support = max(model.k_max, x_max + 500)
    else:  # normal
        k_support = max(2000, x_max + 1000)

    pmf = np.array([model.pmf(k) for k in range(k_support + 1)], dtype=float)
    pmf[pmf < 0] = 0.0
    s = float(pmf.sum())
    # remaining tail mass (should be tiny)
    tail_prob = max(0.0, 1.0 - s)

    ks = np.arange(k_support + 1, dtype=float)

    # Total mean
    if isinstance(model, (ExponentialRoundedDemand, PoissonDemand)):
        mean_d = float(model.mean())
    else:
        # normal: estimate from pmf; tail is negligible at k_support
        mean_d = float((ks * pmf).sum())

    # prefix sums
    cdf = np.cumsum(pmf)               # P(D<=k)
    s2 = np.cumsum(ks * pmf)           # sum_{j<=k} j pmf(j)

    # pad with cdf[-1] for easy indexing
    cdf = np.concatenate(([0.0], cdf))  # cdf[i] = P(D<=i-1)
    s2 = np.concatenate(([0.0], s2))    # s2[i]  = sum_{j<=i-1} j pmf(j)

    costs = np.zeros(x_max + 1, dtype=float)
    for x in range(0, x_max + 1):
        # Using arrays up to k_support; tail beyond is ignored, but tail_prob is tiny by construction.
        C = cdf[x + 1] if (x + 1) < len(cdf) else 1.0
        S = s2[x + 1] if (x + 1) < len(s2) else mean_d

        # E[(x-D)+] = x*C - S
        E_hold = x * C - S
        # E[(D-x)+] = (E[D] - S) - x*(1-C)
        E_lost = (mean_d - S) - x * (1.0 - C)

        costs[x] = h * E_hold + p * E_lost

    return costs


# ----------------------------
# Parametric stochastic DP for L=2
# ----------------------------
def solve_parametric_stochastic_dp_L2(
    instance: dict,
    grid_step: int = 10,
    bound_k_sigma: float = 5.0,
) -> Tuple[List[np.ndarray], float, DPConfigL2]:
    """
    Approximate finite-horizon stochastic DP for lead_time = 2, on a coarse grid.

    State at time t (decision epoch): (x, y)
      x = on-hand after receiving arrivals at start of period t
      y = quantity scheduled to arrive at start of period t+1

    Action: q (arrives at start of t+2)

    Transition:
      D_t realized
      end_inv = max(x - D_t, 0)
      x_{t+1} = end_inv + y
      y_{t+1} = q

    Cost:
      for t >= lead_time: holding_cost * end_inv + lost_sales_cost * (D_t - x)+
      for t <  lead_time: cost is treated as 0 (consistent with the padded-demand setting)

    Returns:
      policy[t][ix,iy] = optimal q index (q = q_index * grid_step)
      V0 = approximate expected optimal total cost from initial state (0,0)
      config
    """
    L = int(instance["lead_time"])
    if L != 2:
        raise NotImplementedError("This implementation is specialized for lead_time = 2.")

    N = int(instance["num_periods"])
    holding_cost = float(instance["holding_cost"])
    lost_sales_cost = float(instance["lost_sales_cost"])

    model = build_model_from_instance(instance)
    mu = float(model.mean())
    std = estimate_std_for_bounds(model)

    y_max = ceil_to_step(mu + bound_k_sigma * std, grid_step)
    x_max = 2 * y_max  # allow inventory accumulation under low demand

    Ny = y_max // grid_step + 1
    Nx = x_max // grid_step + 1
    T = L + N

    config = DPConfigL2(
        step=grid_step, x_max=x_max, y_max=y_max,
        Nx=Nx, Ny=Ny, lead_time=L, horizon=T
    )

    # Precompute immediate expected costs as a function of *integer* x, then sample on the grid.
    imm_cost_int = precompute_immediate_costs(model, holding_cost, lost_sales_cost, x_max)
    imm_cost = np.array([imm_cost_int[ix * grid_step] for ix in range(Nx)], dtype=float)

    # Precompute transition weights w_x for each grid x level.
    # We discretize end inventory by flooring to the grid:
    #   end_inv_grid = step * floor(end_inv / step)
    # These weights depend only on the current x grid level.
    weights_x: List[np.ndarray] = []
    for ix in range(Nx):
        X = ix * grid_step
        w = np.zeros(ix + 1, dtype=float)

        # m=0 corresponds to end_inv_grid = 0, which happens when demand is large enough.
        # Demand threshold for end_inv < step: d >= X - step + 1.
        cutoff = X - grid_step
        w0 = 1.0 - model.cdf(cutoff)  # P(D > cutoff) = P(D >= cutoff+1)
        w[0] = max(0.0, min(1.0, w0))

        # m>=1 corresponds to end_inv_grid = m*step,
        # which means end_inv in [m*step, (m+1)*step - 1].
        for m in range(1, ix + 1):
            a = X - (m + 1) * grid_step + 1  # lower bound on demand
            b = X - m * grid_step            # upper bound on demand
            if b < 0:
                w[m] = 0.0
                continue
            if a <= 0:
                w[m] = model.cdf(b)
            else:
                w[m] = model.cdf(b) - model.cdf(a - 1)
            if w[m] < 0.0:
                w[m] = 0.0

        # normalize to avoid numerical drift
        s = float(w.sum())
        if s <= 0.0:
            w[0] = 1.0
        else:
            w /= s
        weights_x.append(w)

    # Backward DP
    V_next = np.zeros((Nx, Ny), dtype=float)  # terminal cost-to-go at t=T is 0
    policy: List[np.ndarray] = [np.zeros((Nx, Ny), dtype=np.int32) for _ in range(T)]

    y_idx = np.arange(Ny, dtype=int)
    x_cap = Nx - 1

    for t in range(T - 1, -1, -1):
        V_curr = np.empty_like(V_next)
        pi_t = policy[t]

        if t < L:
            # Padded-demand periods: D_t = 0 and cost = 0 in your setup.
            # end_inv = x, next_x = x + y, next_y = q
            # So:
            #   V_t(x,y) = min_q V_{t+1}(min(x+y, x_max), q)
            row_min = V_next.min(axis=1)
            row_arg = V_next.argmin(axis=1)
            for ix in range(Nx):
                nx = np.minimum(ix + y_idx, x_cap)
                V_curr[ix, :] = row_min[nx]
                pi_t[ix, :] = row_arg[nx]
        else:
            # Stochastic demand with expected immediate cost imm_cost[ix].
            for ix in range(Nx):
                w = weights_x[ix]  # length ix+1

                # expected_future[y, q] = sum_m w[m] * V_next[min(y+m, x_cap), q]
                expected_future = np.zeros((Ny, Ny), dtype=float)
                for m, wm in enumerate(w):
                    if wm == 0.0:
                        continue
                    idx = np.minimum(y_idx + m, x_cap)  # length Ny
                    expected_future += wm * V_next[idx, :]

                min_vals = expected_future.min(axis=1)     # for each y, minimize over q
                argmins = expected_future.argmin(axis=1)

                V_curr[ix, :] = imm_cost[ix] + min_vals
                pi_t[ix, :] = argmins

        V_next = V_curr

    V0 = float(V_next[0, 0])
    return policy, V0, config


# ----------------------------
# Policy evaluation on realized trajectories (simulation)
# ----------------------------
def simulate_policy_on_trajectory_L2(instance: dict, policy: List[np.ndarray], config: DPConfigL2) -> float:
    L = int(instance["lead_time"])
    if L != 2:
        raise NotImplementedError("This evaluation routine is specialized for lead_time = 2.")

    N = int(instance["num_periods"])
    holding_cost = float(instance["holding_cost"])
    lost_sales_cost = float(instance["lost_sales_cost"])

    demand_seq = [0] * L + list(instance["demand"])
    T = L + N

    step = config.step
    x_cap = config.Nx - 1
    y_cap = config.Ny - 1

    on_hand = int(instance["initial_inventory"])
    pipeline = [0, 0]  # [arrives now, arrives next period]

    total_cost = 0.0
    for t in range(T):
        # receive arrivals scheduled for now
        on_hand += pipeline[0]
        y_next_period = pipeline[1]

        # map to grid indices (floor)
        ix = min(on_hand // step, x_cap)
        iy = min(y_next_period // step, y_cap)

        q_idx = int(policy[t][ix, iy])
        q = q_idx * step

        # advance pipeline
        pipeline = [pipeline[1], q]

        d = int(demand_seq[t])
        sales = min(on_hand, d)
        lost = d - sales
        on_hand -= sales

        # cost is counted after the padded lead-time periods
        if t >= L:
            total_cost += holding_cost * on_hand + lost_sales_cost * lost

    return total_cost


# ----------------------------
# Main runner
# ----------------------------
def run_for_file(filepath: str, grid_step: int = 10, bound_k_sigma: float = 5.0) -> None:
    if not os.path.exists(filepath):
        print(f"[SKIP] File not found: {filepath}")
        return

    with open(filepath, "r") as f:
        data = json.load(f)

    if not data:
        print(f"[SKIP] Empty file: {filepath}")
        return

    # Basic metadata checks
    first = data[0]
    L = int(first["lead_time"])
    N = int(first["num_periods"])
    h = float(first["holding_cost"])
    p = float(first["lost_sales_cost"])
    dist = str(first.get("distribution", "")).lower()

    print("=" * 80)
    print(f"File: {os.path.basename(filepath)}")
    # print(f"Trajectories: {len(data)}")
    # print(f"Distribution: {dist}")
    # print(f"Lead time (L): {L}")
    # print(f"Demand periods (N): {N}")
    # print(f"Holding cost (h): {h}")
    # print(f"Lost sales cost (p): {p}")
    # if dist == "normal":
    #     print(f"Normal std (std_normal): {first.get('std_normal', None)}")
    # print("-" * 80)

    # Solve DP once per file (parametric)
    t0 = time.time()
    policy, V0, config = solve_parametric_stochastic_dp_L2(
        first, grid_step=grid_step, bound_k_sigma=bound_k_sigma
    )
    t1 = time.time()

    # print("DP configuration:")
    # print(f"  grid_step: {config.step}")
    # print(f"  y_max:      {config.y_max}")
    # print(f"  x_max:      {config.x_max}")
    # print(f"  Ny (y grid points): {config.Ny}")
    # print(f"  Nx (x grid points): {config.Nx}")
    # print(f"  Horizon (L+N):      {config.horizon}")
    # print(f"DP solve time: {t1 - t0:.2f} seconds")
    # print(f"Approx. expected optimal cost from initial state (0,0): {V0:.4f}")

    # Evaluate on all trajectories
    costs = [simulate_policy_on_trajectory_L2(inst, policy, config) for inst in data]
    mean_cost = statistics.mean(costs)
    std_cost = statistics.pstdev(costs) if len(costs) > 1 else 0.0

    # print("-" * 80)
    print("Policy evaluation on realized trajectories:")
    print(f"  Mean total cost: {mean_cost:.4f}")
    print(f"  Std. dev. cost:  {std_cost:.4f}")
    print(f"  Min cost:        {min(costs):.4f}")
    print(f"  Max cost:        {max(costs):.4f}")


def main() -> None:
    # Files required by your prompt
    files = [
        "exponential_L2_c1_2_train.json",
        "normal_std30_L2_c1_2_train.json",
        "poisson_L2_c1_2_train.json",
    ]

    # You can tune these trade-offs:
    # - larger grid_step => faster but coarser policy (orders become multiples of grid_step)
    # - larger bound_k_sigma => larger state/action ranges => more compute
    grid_step = 10
    bound_k_sigma = 5.0

    for fn in files:
        run_for_file(fn, grid_step=grid_step, bound_k_sigma=bound_k_sigma)

    print("=" * 80)
    print("Done.")


if __name__ == "__main__":
    main()
