import numpy as np
import json
import os
from datetime import datetime
import glob

# ----------------------------
# Core instance generation
# ----------------------------
def _sample_demand(dist: str, num_periods: int, *, std_normal: int | None = None, pareto_alpha: float = 3.0):
    """
    Return an integer demand array of length num_periods with theoretical mean 100.
    - dist ∈ {'poisson','normal','exponential','pareto','lomax'}
    - For normal, pass std_normal in {10,20,30}; negatives are clipped to 0.
    - For pareto, Type-I Pareto with alpha, scaled so mean=100.
    """
    mean = 100.0

    if dist == "poisson":
        demand = np.random.poisson(lam=mean, size=num_periods).astype(int)

    elif dist == "normal":
        if std_normal is None:
            raise ValueError("std_normal must be provided for normal distribution.")
        x = np.random.normal(loc=mean, scale=float(std_normal), size=num_periods)
        x = np.clip(x, 0, None)               # truncate left side
        demand = np.rint(x).astype(int)

    elif dist == "exponential":
        # numpy uses scale=1/lambda; scale == mean for exponential
        x = np.random.exponential(scale=mean, size=num_periods)
        demand = np.rint(x).astype(int)

    elif dist == "pareto":
        # NumPy Pareto: Y = xm * (1 + X), X ~ Pareto(a) with mean = a/(a-1) for a>1 when xm=1
        # We want E[Y] = xm * a/(a-1) = 100  -> xm = 100 * (a-1)/a
        a = float(pareto_alpha)
        xm = mean * (a - 1.0) / a
        y = xm * (np.random.pareto(a, size=num_periods) + 1.0)
        demand = np.rint(y).astype(int)

    elif dist == "lomax":
        # Lomax(alpha, lambda) with mean lambda/(alpha-1) = 100.
        # In NumPy, np.random.pareto(a) already gives a Lomax(alpha=a, lambda=1)
        # with pdf f(x) = a (1 + x)^(-a-1), x >= 0.
        # So we just scale by lambda = 100 * (a - 1).
        a = float(pareto_alpha)
        if a <= 1.0:
            raise ValueError("pareto_alpha (shape for lomax) must be > 1 for finite mean.")
        lam = mean * (a - 1.0)   # so that lam/(a-1) = mean = 100
        y = lam * np.random.pareto(a, size=num_periods)
        demand = np.rint(y).astype(int)

    else:
        raise ValueError(f"Unknown dist: {dist}")

    return demand.tolist()


def generate_random_instance(
    dist: str,
    num_periods: int = 50,
    lead_time: int = 1,
    initial_inventory: int | None = 80,
    holding_cost: float = 2.0,
    lost_sales_cost: float = 10.0,
    std_normal: int | None = None,
    pareto_alpha: float = 3.0,
    instance_id: str | None = None,
):
    """
    Generate one inventory instance with demand of length num_periods.
    Output format matches the existing code (a dict with the same keys).
    """
    if initial_inventory is None:
        initial_inventory = np.random.randint(60, 100)

    demand = _sample_demand(dist, num_periods, std_normal=std_normal, pareto_alpha=pareto_alpha)

    if instance_id is None:
        instance_id = f"instance_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    return {
        "instance_id": instance_id,
        "initial_inventory": initial_inventory,
        "demand": demand,
        "num_periods": num_periods,
        "holding_cost": holding_cost,
        "lost_sales_cost": lost_sales_cost,
        "lead_time": lead_time,
        "distribution": dist,
        "std_normal": std_normal,
        "pareto_alpha": pareto_alpha,
    }


# ----------------------------
# I/O helpers (unchanged format)
# ----------------------------
def save_instances(instances, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(instances, f, indent=4)
    print(f"Saved {len(instances)} instances to {file_path}")


def load_instances(pattern):
    instances = []
    for file_path in glob.glob(pattern):
        with open(file_path, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                instances.extend(data)
            else:
                instances.append(data)
    return instances


# ----------------------------
# Dataset builder
# ----------------------------
if __name__ == "__main__":
    np.random.seed()  # or set a fixed seed if you want reproducibility

    num_periods = 50
    initial_inventory = 0
    lead_times = [2, 4, 6]
    cost_pairs = [(1, 2), (1, 5)]

    # Distributions to generate
    dists = ["poisson", "exponential"]
    normal_stds = [10, 30, 50]  # only used for 'normal'

    # how many trajectories per file
    N_TEST = 1000
    N_TRAIN = 100

    # ---------- NORMAL (three std levels) ----------
    for std in normal_stds:
        for L in lead_times:
            for hc, lc in cost_pairs:
                # test
                test_instances = [
                    generate_random_instance(
                        dist="normal",
                        num_periods=num_periods,
                        lead_time=L,
                        initial_inventory=initial_inventory,
                        holding_cost=hc,
                        lost_sales_cost=lc,
                        std_normal=std,
                        instance_id=f"test_normstd{std}_L{L}_c{hc}_{lc}_{i}",
                    )
                    for i in range(N_TEST)
                ]
                save_instances(
                    test_instances,
                    f"data/normal_std{std}_L{L}_c{hc}_{lc}_test.json",
                )

                # train
                train_instances = [
                    generate_random_instance(
                        dist="normal",
                        num_periods=num_periods,
                        lead_time=L,
                        initial_inventory=initial_inventory,
                        holding_cost=hc,
                        lost_sales_cost=lc,
                        std_normal=std,
                        instance_id=f"train_normstd{std}_L{L}_c{hc}_{lc}_{i}",
                    )
                    for i in range(N_TRAIN)
                ]
                save_instances(
                    train_instances,
                    f"data/normal_std{std}_L{L}_c{hc}_{lc}_train.json",
                )

    # ---------- OTHER DISTS (single config each) ----------
    for dist in dists:  # poisson, exponential, pareto, lomax
        for L in lead_times:
            for hc, lc in cost_pairs:
                # test
                test_instances = [
                    generate_random_instance(
                        dist=dist,
                        num_periods=num_periods,
                        lead_time=L,
                        initial_inventory=initial_inventory,
                        holding_cost=hc,
                        lost_sales_cost=lc,
                        instance_id=f"test_{dist}_L{L}_c{hc}_{lc}_{i}",
                    )
                    for i in range(N_TEST)
                ]
                save_instances(
                    test_instances,
                    f"data/{dist}_L{L}_c{hc}_{lc}_test.json",
                )

                # train
                train_instances = [
                    generate_random_instance(
                        dist=dist,
                        num_periods=num_periods,
                        lead_time=L,
                        initial_inventory=initial_inventory,
                        holding_cost=hc,
                        lost_sales_cost=lc,
                        instance_id=f"train_{dist}_L{L}_c{hc}-{lc}_{i}",
                    )
                    for i in range(N_TRAIN)
                ]
                save_instances(
                    train_instances,
                    f"data/{dist}_L{L}_c{hc}_{lc}_train.json",
                )
