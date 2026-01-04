import numpy as np
import json
import os
from datetime import datetime
import glob

# ----------------------------
# Demand sampling (catalog-driven)
# ----------------------------
def _round_clip_nonneg(x: float) -> int:
    """Round to nearest int and clip to nonnegative."""
    y = int(np.rint(x))
    return y if y > 0 else 0


def _fmt_num(x) -> str:
    """Format numbers for tags/filenames without dots."""
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    # keep a compact representation (e.g., 0.05 -> 0p05)
    s = f"{float(x):g}"
    return s.replace(".", "p").replace("-", "m")


def _sample_demand(family: str, num_periods: int, **params):
    """
    Return an integer demand list of length num_periods.

    Supported families (per MD catalog):
      - negbin: Negative Binomial NB(r, p)
      - binomial: Binomial(n, p)
      - geometric0: Geometric(p) with support {0,1,2,...} (implemented as geometric-1)
      - dunif: Discrete Uniform {L,...,H} (inclusive)
      - zinb: Zero-inflated Negative Binomial (pi0, r, p)
      - cunif: Continuous Uniform(a, b) mapped to integer
      - normal: Normal(mu, sigma) mapped to integer with nonneg clipping
      - triangular: Triangular(a, c, b) mapped to integer
      - beta_scaled: M * Beta(a, b) mapped to integer
      - lognormal: LogNormal(mu_log, sigma) mapped to integer
      - gamma: Gamma(k, theta) mapped to integer
      - weibull: Weibull(k) * lam mapped to integer
      - pareto: Type-I Pareto(alpha, xm) mapped to integer
    """
    fam = family.lower()

    if fam == "negbin":
        r = int(params["r"])
        p = float(params["p"])
        d = np.random.negative_binomial(n=r, p=p, size=num_periods).astype(int)

    elif fam == "binomial":
        n = int(params["n"])
        p = float(params["p"])
        d = np.random.binomial(n=n, p=p, size=num_periods).astype(int)

    elif fam == "geometric0":
        p = float(params["p"])
        d = (np.random.geometric(p=p, size=num_periods) - 1).astype(int)

    elif fam == "dunif":
        L = int(params["L"])
        H = int(params["H"])
        if H <= L:
            raise ValueError("DiscreteUniform requires H > L.")
        d = np.random.randint(L, H + 1, size=num_periods).astype(int)

    elif fam == "zinb":
        pi0 = float(params["pi0"])
        r = int(params["r"])
        p = float(params["p"])
        u = np.random.random(size=num_periods)
        d_nb = np.random.negative_binomial(n=r, p=p, size=num_periods).astype(int)
        d = np.where(u < pi0, 0, d_nb).astype(int)

    elif fam == "cunif":
        a = float(params["a"])
        b = float(params["b"])
        if b <= a:
            raise ValueError("Uniform(a,b) requires b > a.")
        x = np.random.uniform(low=a, high=b, size=num_periods)
        d = np.array([_round_clip_nonneg(v) for v in x], dtype=int)

    elif fam == "normal":
        mu = float(params["mu"])
        sigma = float(params["sigma"])
        x = np.random.normal(loc=mu, scale=sigma, size=num_periods)
        d = np.array([_round_clip_nonneg(v) for v in x], dtype=int)

    elif fam == "triangular":
        a = float(params["a"])
        c = float(params["c"])
        b = float(params["b"])
        if not (a < c < b):
            raise ValueError("Triangular requires a < c < b.")
        x = np.random.triangular(left=a, mode=c, right=b, size=num_periods)
        d = np.array([_round_clip_nonneg(v) for v in x], dtype=int)

    elif fam == "beta_scaled":
        aa = float(params["a"])
        bb = float(params["b"])
        M = float(params["M"])
        x = np.random.beta(a=aa, b=bb, size=num_periods) * M
        d = np.array([_round_clip_nonneg(v) for v in x], dtype=int)

    elif fam == "lognormal":
        mu_log = float(params["mu_log"])
        sigma = float(params["sigma"])
        x = np.random.lognormal(mean=mu_log, sigma=sigma, size=num_periods)
        d = np.array([_round_clip_nonneg(v) for v in x], dtype=int)

    elif fam == "gamma":
        k = float(params["k"])
        theta = float(params["theta"])
        x = np.random.gamma(shape=k, scale=theta, size=num_periods)
        d = np.array([_round_clip_nonneg(v) for v in x], dtype=int)

    elif fam == "weibull":
        k = float(params["k"])
        lam = float(params["lam"])
        x = np.random.weibull(a=k, size=num_periods) * lam
        d = np.array([_round_clip_nonneg(v) for v in x], dtype=int)

    elif fam == "pareto":
        alpha = float(params["alpha"])
        xm = float(params["xm"])
        # NumPy Pareto: (pareto(alpha) + 1) has Type-I Pareto with xm=1
        x = (np.random.pareto(a=alpha, size=num_periods) + 1.0) * xm
        d = np.array([_round_clip_nonneg(v) for v in x], dtype=int)

    else:
        raise ValueError(f"Unknown family: {family}")

    return d.tolist()


def _dist_tag(family: str, **params) -> str:
    """Build a stable tag for filenames and instance_id."""
    fam = family.lower()

    if fam == "negbin":
        return f"negbin_r{_fmt_num(params['r'])}_p{_fmt_num(params['p'])}"
    if fam == "binomial":
        return f"binom_n{_fmt_num(params['n'])}_p{_fmt_num(params['p'])}"
    if fam == "geometric0":
        return f"geom_p{_fmt_num(params['p'])}"
    if fam == "dunif":
        return f"dunif_L{_fmt_num(params['L'])}_H{_fmt_num(params['H'])}"
    if fam == "zinb":
        return f"zinb_pi{_fmt_num(params['pi0'])}_r{_fmt_num(params['r'])}_p{_fmt_num(params['p'])}"
    if fam == "cunif":
        return f"cunif_a{_fmt_num(params['a'])}_b{_fmt_num(params['b'])}"
    if fam == "normal":
        return f"normal_mu{_fmt_num(params['mu'])}_sd{_fmt_num(params['sigma'])}"
    if fam == "triangular":
        return f"tri_a{_fmt_num(params['a'])}_c{_fmt_num(params['c'])}_b{_fmt_num(params['b'])}"
    if fam == "beta_scaled":
        return f"beta_a{_fmt_num(params['a'])}_b{_fmt_num(params['b'])}_M{_fmt_num(params['M'])}"
    if fam == "lognormal":
        return f"logn_mlog{_fmt_num(params['mu_log'])}_s{_fmt_num(params['sigma'])}"
    if fam == "gamma":
        return f"gamma_k{_fmt_num(params['k'])}_th{_fmt_num(params['theta'])}"
    if fam == "weibull":
        return f"weib_k{_fmt_num(params['k'])}_lam{_fmt_num(params['lam'])}"
    if fam == "pareto":
        return f"pareto_a{_fmt_num(params['alpha'])}_xm{_fmt_num(params['xm'])}"

    return fam


def build_distribution_specs():
    """
    Build the full set of distribution specs required by the MD catalog.
    Returns a list of tuples: (family, params_dict).
    """
    specs = []

    # A1 Negative Binomial
    for r in [2, 5, 10, 20, 40]:
        for p in [0.1, 0.2, 0.3, 0.4, 0.6, 0.8]:
            specs.append(("negbin", {"r": r, "p": p}))

    # A2 Binomial
    for n in [20, 50, 100, 200, 400, 800]:
        for p in [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 0.95]:
            specs.append(("binomial", {"n": n, "p": p}))

    # A3 Geometric (0-based)
    for p in [0.03, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3, 0.4, 0.6, 0.8]:
        specs.append(("geometric0", {"p": p}))

    # A4 Discrete Uniform
    Ls = [0, 5, 10, 20, 50]
    Hs = [20, 50, 100, 200, 400, 800]
    for L in Ls:
        for H in Hs:
            if H > L:
                specs.append(("dunif", {"L": L, "H": H}))

    # B1 ZINB
    for pi0 in [0.1, 0.3, 0.5, 0.7, 0.85]:
        for r in [2, 5, 10, 20, 40]:
            for p in [0.1, 0.2, 0.3, 0.4, 0.6, 0.8]:
                specs.append(("zinb", {"pi0": pi0, "r": r, "p": p}))

    # C1 Continuous Uniform
    for a in [0, 10, 20, 50]:
        for b in [50, 100, 200, 400, 800]:
            if b > a:
                specs.append(("cunif", {"a": a, "b": b}))

    # C2 Normal with sigma = {10%, 15%, 20%, 25%, 30%} of mean; exclude (100,10),(100,30),(100,50)
    mus = [20, 50, 80, 100, 150, 200, 300]
    frac = [0.10, 0.15, 0.20, 0.25, 0.30]
    excluded = {(100, 10), (100, 30), (100, 50)}
    for mu in mus:
        for f in frac:
            sigma = int(round(mu * f))
            if (mu, sigma) in excluded:
                continue
            specs.append(("normal", {"mu": mu, "sigma": sigma}))

    # C3 Triangular
    for a in [0, 5, 10]:
        for c in [20, 50, 100, 200]:
            for b in [60, 120, 250, 500, 800]:
                if a < c < b:
                    specs.append(("triangular", {"a": a, "c": c, "b": b}))

    # C4 Beta scaled
    for aa in [0.5, 1, 2, 5, 10]:
        for bb in [0.5, 1, 2, 5, 10]:
            for M in [20, 50, 100, 200, 500]:
                specs.append(("beta_scaled", {"a": aa, "b": bb, "M": M}))

    # D1 Lognormal
    for mu_log in [1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
        for sigma in [0.3, 0.5, 0.7, 1.0, 1.3]:
            specs.append(("lognormal", {"mu_log": mu_log, "sigma": sigma}))

    # D2 Gamma
    for k in [0.8, 1, 2, 5, 10, 20]:
        for theta in [2, 5, 10, 20, 40, 80]:
            specs.append(("gamma", {"k": k, "theta": theta}))

    # D3 Weibull
    for k in [0.8, 1.2, 1.8, 2.5, 3.5, 5.0]:
        for lam in [10, 30, 60, 100, 200, 500]:
            specs.append(("weibull", {"k": k, "lam": lam}))

    # D4 Pareto
    for alpha in [1.3, 1.5, 2.0, 3.0, 4.0, 6.0]:
        for xm in [1, 5, 10, 20, 50, 100]:
            specs.append(("pareto", {"alpha": alpha, "xm": xm}))

    return specs


# ----------------------------
# Core instance generation
# ----------------------------
def generate_random_instance(
    family: str,
    dist_params: dict,
    num_periods: int = 50,
    lead_time: int = 1,
    initial_inventory: int | None = 80,
    holding_cost: float = 2.0,
    lost_sales_cost: float = 10.0,
    instance_id: str | None = None,
):
    """
    Generate one inventory instance with demand of length num_periods.
    Output format matches the existing code (same keys). We only change the demand data.

    Notes:
    - distribution field is a tag that encodes the family and parameters.
    - std_normal and pareto_alpha are retained for backward compatibility; they are set
      when applicable, otherwise left as None.
    """
    if initial_inventory is None:
        initial_inventory = np.random.randint(60, 100)

    demand = _sample_demand(family, num_periods, **dist_params)
    dist_tag = _dist_tag(family, **dist_params)

    # Backward-compatible fields (existing keys)
    std_normal = None
    pareto_alpha = None
    if family.lower() == "normal":
        std_normal = int(dist_params.get("sigma"))
    if family.lower() == "pareto":
        pareto_alpha = float(dist_params.get("alpha"))

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
        "distribution": dist_tag,
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
    lead_times = [6]
    cost_pairs = [(1, 2)]

    # how many trajectories per file
    N_TEST = 1000
    N_TRAIN = 100

    specs = build_distribution_specs()

    for family, dist_params in specs:
        dist_tag = _dist_tag(family, **dist_params)

        for L in lead_times:
            for hc, lc in cost_pairs:
                # test
                test_instances = [
                    generate_random_instance(
                        family=family,
                        dist_params=dist_params,
                        num_periods=num_periods,
                        lead_time=L,
                        initial_inventory=initial_inventory,
                        holding_cost=hc,
                        lost_sales_cost=lc,
                        instance_id=f"test_{dist_tag}_L{L}_c{hc}_{lc}_{i}",
                    )
                    for i in range(N_TEST)
                ]
                save_instances(
                    test_instances,
                    f"./{dist_tag}_L{L}_c{hc}_{lc}_test.json",
                )

                # train
                train_instances = [
                    generate_random_instance(
                        family=family,
                        dist_params=dist_params,
                        num_periods=num_periods,
                        lead_time=L,
                        initial_inventory=initial_inventory,
                        holding_cost=hc,
                        lost_sales_cost=lc,
                        instance_id=f"train_{dist_tag}_L{L}_c{hc}_{lc}_{i}",
                    )
                    for i in range(N_TRAIN)
                ]
                save_instances(
                    train_instances,
                    f"./{dist_tag}_L{L}_c{hc}_{lc}_train.json",
                )
