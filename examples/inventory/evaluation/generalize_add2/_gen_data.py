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
    xf = float(x)
    if xf.is_integer():
        return str(int(xf))
    s = f"{xf:g}"
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
      - exponential: Exponential(rate) mapped to integer
      - poisson: Poisson(lam)
    """
    fam = family.lower()

    if fam == "negbin":
        r = float(params["r"])
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
        r = float(params["r"])
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
        if not (a <= c <= b and a < b):
            raise ValueError("Triangular requires a <= c <= b and a < b.")
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

    elif fam == "exponential":
        rate = float(params["rate"])
        if rate <= 0:
            raise ValueError("Exponential requires rate > 0.")
        x = np.random.exponential(scale=1.0 / rate, size=num_periods)
        d = np.array([_round_clip_nonneg(v) for v in x], dtype=int)

    elif fam == "poisson":
        lam = float(params["lam"])
        if lam < 0:
            raise ValueError("Poisson requires lam >= 0.")
        d = np.random.poisson(lam=lam, size=num_periods).astype(int)


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
    if fam == "exponential":
        return f"exponential_rate{_fmt_num(params['rate'])}"
    if fam == "poisson":
        return f"poisson_lam{_fmt_num(params['lam'])}"

    return fam


def build_distribution_specs():
    """
    Hard-coded unique distribution specs derived from the Excel requirements.
    Each (family, params) configuration appears exactly once.
    """
    specs = [('beta_scaled', {'a': 22.4, 'b': 201.6, 'M': 500}),
 ('beta_scaled', {'a': 5.525, 'b': 49.725, 'M': 500}),
 ('beta_scaled', {'a': 2.4, 'b': 21.6, 'M': 500}),
 ('beta_scaled', {'a': 0.8, 'b': 7.2, 'M': 500}),
 ('beta_scaled', {'a': 0.125, 'b': 1.125, 'M': 500}),
 ('beta_scaled', {'a': 47.6625, 'b': 270.0875, 'M': 500}),
 ('beta_scaled', {'a': 11.803125, 'b': 66.884375, 'M': 500}),
 ('beta_scaled', {'a': 5.1625, 'b': 29.25416667, 'M': 500}),
 ('beta_scaled', {'a': 1.7625, 'b': 9.9875, 'M': 500}),
 ('beta_scaled', {'a': 0.328125, 'b': 1.859375, 'M': 500}),
 ('beta_scaled', {'a': 79.8, 'b': 319.2, 'M': 500}),
 ('beta_scaled', {'a': 19.8, 'b': 79.2, 'M': 500}),
 ('beta_scaled', {'a': 8.688888889, 'b': 34.75555556, 'M': 500}),
 ('beta_scaled', {'a': 3, 'b': 12, 'M': 500}),
 ('beta_scaled', {'a': 0.6, 'b': 2.4, 'M': 500}),
 ('beta_scaled', {'a': 116.9375, 'b': 350.8125, 'M': 500}),
 ('beta_scaled', {'a': 29.046875, 'b': 87.140625, 'M': 500}),
 ('beta_scaled', {'a': 12.77083333, 'b': 38.3125, 'M': 500}),
 ('beta_scaled', {'a': 4.4375, 'b': 13.3125, 'M': 500}),
 ('beta_scaled', {'a': 0.921875, 'b': 2.765625, 'M': 500}),
 ('beta_scaled', {'a': 157.2, 'b': 366.8, 'M': 500}),
 ('beta_scaled', {'a': 39.075, 'b': 91.175, 'M': 500}),
 ('beta_scaled', {'a': 17.2, 'b': 40.13333333, 'M': 500}),
 ('beta_scaled', {'a': 6, 'b': 14, 'M': 500}),
 ('beta_scaled', {'a': 1.275, 'b': 2.975, 'M': 500}),
 ('binomial', {'n': 500000, 'p': 0.0001}),
 ('binomial', {'n': 750000, 'p': 0.0001}),
 ('binomial', {'n': 1000000, 'p': 0.0001}),
 ('binomial', {'n': 625, 'p': 0.2}),
 ('binomial', {'n': 1250000, 'p': 0.0001}),
 ('binomial', {'n': 450, 'p': 0.333333333}),
 ('binomial', {'n': 1500000, 'p': 0.0001}),
 ('cunif', {'a': 32.67949192, 'b': 67.32050808}),
 ('cunif', {'a': 15.35898385, 'b': 84.64101615}),
 ('cunif', {'a': 0, 'b': 100}),
 ('cunif', {'a': 57.67949192, 'b': 92.32050808}),
 ('cunif', {'a': 40.35898385, 'b': 109.6410162}),
 ('cunif', {'a': 23.03847577, 'b': 126.9615242}),
 ('cunif', {'a': 0, 'b': 150}),
 ('cunif', {'a': 82.67949192, 'b': 117.3205081}),
 ('cunif', {'a': 65.35898385, 'b': 134.6410162}),
 ('cunif', {'a': 48.03847577, 'b': 151.9615242}),
 ('cunif', {'a': 13.39745962, 'b': 186.6025404}),
 ('cunif', {'a': 0, 'b': 200}),
 ('cunif', {'a': 107.6794919, 'b': 142.3205081}),
 ('cunif', {'a': 90.35898385, 'b': 159.6410162}),
 ('cunif', {'a': 73.03847577, 'b': 176.9615242}),
 ('cunif', {'a': 38.39745962, 'b': 211.6025404}),
 ('cunif', {'a': 0, 'b': 250}),
 ('cunif', {'a': 132.6794919, 'b': 167.3205081}),
 ('cunif', {'a': 115.3589838, 'b': 184.6410162}),
 ('cunif', {'a': 98.03847577, 'b': 201.9615242}),
 ('cunif', {'a': 63.39745962, 'b': 236.6025404}),
 ('cunif', {'a': 0, 'b': 300}),
 ('dunif', {'L': 33, 'H': 67}),
 ('dunif', {'L': 16, 'H': 84}),
 ('dunif', {'L': 0, 'H': 100}),
 ('dunif', {'L': 58, 'H': 92}),
 ('dunif', {'L': 41, 'H': 109}),
 ('dunif', {'L': 24, 'H': 126}),
 ('dunif', {'L': 0, 'H': 150}),
 ('dunif', {'L': 83, 'H': 117}),
 ('dunif', {'L': 66, 'H': 134}),
 ('dunif', {'L': 49, 'H': 151}),
 ('dunif', {'L': 14, 'H': 186}),
 ('dunif', {'L': 0, 'H': 200}),
 ('dunif', {'L': 108, 'H': 142}),
 ('dunif', {'L': 91, 'H': 159}),
 ('dunif', {'L': 74, 'H': 176}),
 ('dunif', {'L': 39, 'H': 211}),
 ('dunif', {'L': 0, 'H': 250}),
 ('dunif', {'L': 133, 'H': 167}),
 ('dunif', {'L': 116, 'H': 184}),
 ('dunif', {'L': 99, 'H': 201}),
 ('dunif', {'L': 64, 'H': 236}),
 ('dunif', {'L': 0, 'H': 300}),
 ('gamma', {'k': 25, 'theta': 2}),
 ('gamma', {'k': 6.25, 'theta': 8}),
 ('gamma', {'k': 2.777777778, 'theta': 18}),
 ('gamma', {'k': 1, 'theta': 50}),
 ('gamma', {'k': 0.25, 'theta': 200}),
 ('gamma', {'k': 56.25, 'theta': 1.333333333}),
 ('gamma', {'k': 14.0625, 'theta': 5.333333333}),
 ('gamma', {'k': 6.25, 'theta': 12}),
 ('gamma', {'k': 2.25, 'theta': 33.33333333}),
 ('gamma', {'k': 0.5625, 'theta': 133.3333333}),
 ('gamma', {'k': 100, 'theta': 1}),
 ('gamma', {'k': 25, 'theta': 4}),
 ('gamma', {'k': 11.11111111, 'theta': 9}),
 ('gamma', {'k': 4, 'theta': 25}),
 ('gamma', {'k': 1, 'theta': 100}),
 ('gamma', {'k': 156.25, 'theta': 0.8}),
 ('gamma', {'k': 39.0625, 'theta': 3.2}),
 ('gamma', {'k': 17.36111111, 'theta': 7.2}),
 ('gamma', {'k': 6.25, 'theta': 20}),
 ('gamma', {'k': 1.5625, 'theta': 80}),
 ('gamma', {'k': 225, 'theta': 0.666666667}),
 ('gamma', {'k': 56.25, 'theta': 2.666666667}),
 ('gamma', {'k': 25, 'theta': 6}),
 ('gamma', {'k': 9, 'theta': 16.66666667}),
 ('gamma', {'k': 2.25, 'theta': 66.66666667}),
 ('geometric0', {'p': 0.019607843}),
 ('geometric0', {'p': 0.013157895}),
 ('geometric0', {'p': 0.00990099}),
 ('geometric0', {'p': 0.007936508}),
 ('geometric0', {'p': 0.006622517}),
 ('lognormal', {'mu_log': 3.892412649, 'sigma': 0.1980422}),
 ('lognormal', {'mu_log': 3.837813003, 'sigma': 0.38525317}),
 ('lognormal', {'mu_log': 3.758280656, 'sigma': 0.554513029}),
 ('lognormal', {'mu_log': 3.565449415, 'sigma': 0.8325546109999999}),
 ('lognormal', {'mu_log': 3.107304049, 'sigma': 1.268636241}),
 ('lognormal', {'mu_log': 4.308677313, 'sigma': 0.13274638}),
 ('lognormal', {'mu_log': 4.283139848, 'sigma': 0.262100231}),
 ('lognormal', {'mu_log': 4.243278111, 'sigma': 0.38525317}),
 ('lognormal', {'mu_log': 4.133625723, 'sigma': 0.60640315}),
 ('lognormal', {'mu_log': 3.80666249, 'sigma': 1.010767653}),
 ('lognormal', {'mu_log': 4.600195021, 'sigma': 0.099751345}),
 ('lognormal', {'mu_log': 4.585559829, 'sigma': 0.1980422}),
 ('lognormal', {'mu_log': 4.562081338, 'sigma': 0.293560379}),
 ('lognormal', {'mu_log': 4.49359841, 'sigma': 0.472380727}),
 ('lognormal', {'mu_log': 4.258596596, 'sigma': 0.8325546109999999}),
 ('lognormal', {'mu_log': 4.825123934, 'sigma': 0.079872442}),
 ('lognormal', {'mu_log': 4.815674834, 'sigma': 0.158989959}),
 ('lognormal', {'mu_log': 4.800312642, 'sigma': 0.236647819}),
 ('lognormal', {'mu_log': 4.754103735, 'sigma': 0.38525317}),
 ('lognormal', {'mu_log': 4.580965616, 'sigma': 0.703346459}),
 ('lognormal', {'mu_log': 5.008417996, 'sigma': 0.06659277}),
 ('lognormal', {'mu_log': 5.001824493, 'sigma': 0.13274638}),
 ('lognormal', {'mu_log': 4.991024938, 'sigma': 0.1980422}),
 ('lognormal', {'mu_log': 4.957955036, 'sigma': 0.324592846}),
 ('lognormal', {'mu_log': 4.826772904, 'sigma': 0.60640315}),
 ('negbin', {'r': 50, 'p': 0.5}),
 ('negbin', {'r': 7.142857143, 'p': 0.125}),
 ('negbin', {'r': 2.941176471, 'p': 0.055555556}),
 ('negbin', {'r': 1.020408163, 'p': 0.02}),
 ('negbin', {'r': 0.251256281, 'p': 0.005}),
 ('negbin', {'r': 225, 'p': 0.75}),
 ('negbin', {'r': 17.30769231, 'p': 0.1875}),
 ('negbin', {'r': 6.818181818, 'p': 0.083333333}),
 ('negbin', {'r': 2.319587629, 'p': 0.03}),
 ('negbin', {'r': 0.56675063, 'p': 0.0075}),
 ('negbin', {'r': 99900, 'p': 0.999}),
 ('negbin', {'r': 33.33333333, 'p': 0.25}),
 ('negbin', {'r': 12.5, 'p': 0.111111111}),
 ('negbin', {'r': 4.166666667, 'p': 0.04}),
 ('negbin', {'r': 1.01010101, 'p': 0.01}),
 ('negbin', {'r': 124875, 'p': 0.999}),
 ('negbin', {'r': 56.81818182, 'p': 0.3125}),
 ('negbin', {'r': 20.16129032, 'p': 0.138888889}),
 ('negbin', {'r': 6.578947368, 'p': 0.05}),
 ('negbin', {'r': 1.582278481, 'p': 0.0125}),
 ('negbin', {'r': 149850, 'p': 0.999}),
 ('negbin', {'r': 90, 'p': 0.375}),
 ('negbin', {'r': 30, 'p': 0.166666667}),
 ('negbin', {'r': 9.574468085, 'p': 0.06}),
 ('negbin', {'r': 2.284263959, 'p': 0.015}),
 ('normal', {'mu': 50, 'sigma': 10}),
 ('normal', {'mu': 50, 'sigma': 20}),
 ('normal', {'mu': 50, 'sigma': 30}),
 ('normal', {'mu': 50, 'sigma': 50}),
 ('normal', {'mu': 50, 'sigma': 100}),
 ('normal', {'mu': 75, 'sigma': 10}),
 ('normal', {'mu': 75, 'sigma': 20}),
 ('normal', {'mu': 75, 'sigma': 30}),
 ('normal', {'mu': 75, 'sigma': 50}),
 ('normal', {'mu': 75, 'sigma': 100}),
 ('normal', {'mu': 100, 'sigma': 10}),
 ('normal', {'mu': 100, 'sigma': 20}),
 ('normal', {'mu': 100, 'sigma': 30}),
 ('normal', {'mu': 100, 'sigma': 50}),
 ('normal', {'mu': 100, 'sigma': 100}),
 ('normal', {'mu': 125, 'sigma': 10}),
 ('normal', {'mu': 125, 'sigma': 20}),
 ('normal', {'mu': 125, 'sigma': 30}),
 ('normal', {'mu': 125, 'sigma': 50}),
 ('normal', {'mu': 125, 'sigma': 100}),
 ('normal', {'mu': 150, 'sigma': 10}),
 ('normal', {'mu': 150, 'sigma': 20}),
 ('normal', {'mu': 150, 'sigma': 30}),
 ('normal', {'mu': 150, 'sigma': 50}),
 ('normal', {'mu': 150, 'sigma': 100}),
 ('pareto', {'alpha': 6.099019514, 'xm': 41.80196097}),
 ('pareto', {'alpha': 3.692582404, 'xm': 36.45934077}),
 ('pareto', {'alpha': 2.943650632, 'xm': 33.01428863}),
 ('pareto', {'alpha': 2.414213562, 'xm': 29.28932188}),
 ('pareto', {'alpha': 2.118033989, 'xm': 26.39320225}),
 ('pareto', {'alpha': 8.566372975, 'xm': 66.24483603}),
 ('pareto', {'alpha': 4.881043674, 'xm': 59.63443374}),
 ('pareto', {'alpha': 3.692582404, 'xm': 54.68901116}),
 ('pareto', {'alpha': 2.802775638, 'xm': 48.24081208}),
 ('pareto', {'alpha': 2.25, 'xm': 41.66666667}),
 ('pareto', {'alpha': 11.04987562, 'xm': 90.95012438}),
 ('pareto', {'alpha': 6.099019514, 'xm': 83.60392195}),
 ('pareto', {'alpha': 4.48010217, 'xm': 77.67908047}),
 ('pareto', {'alpha': 3.236067977, 'xm': 69.09830056}),
 ('pareto', {'alpha': 2.414213562, 'xm': 58.57864376}),
 ('pareto', {'alpha': 13.5399362, 'xm': 115.768051}),
 ('pareto', {'alpha': 7.329494451, 'xm': 107.9456178}),
 ('pareto', {'alpha': 5.284986711, 'xm': 101.3480957}),
 ('pareto', {'alpha': 3.692582404, 'xm': 91.14835193}),
 ('pareto', {'alpha': 2.600781059, 'xm': 76.93751525}),
 ('pareto', {'alpha': 16.03329638, 'xm': 140.6444691}),
 ('pareto', {'alpha': 8.566372975, 'xm': 132.4896721}),
 ('pareto', {'alpha': 6.099019514, 'xm': 125.4058829}),
 ('pareto', {'alpha': 4.16227766, 'xm': 113.962039}),
 ('pareto', {'alpha': 2.802775638, 'xm': 96.48162415}),
 ('triangular', {'a': 25.50510257, 'c': 50, 'b': 74.49489743}),
 ('triangular', {'a': 1.010205144, 'c': 50, 'b': 98.98979486}),
 ('triangular', {'a': 0, 'c': 15.62828956, 'b': 134.3717104}),
 ('triangular', {'a': 0, 'c': 0, 'b': 150}),
 ('triangular', {'a': 50.50510257, 'c': 75, 'b': 99.49489743}),
 ('triangular', {'a': 26.01020514, 'c': 75, 'b': 123.9897949}),
 ('triangular', {'a': 1.515307717, 'c': 75, 'b': 148.4846923}),
 ('triangular', {'a': 0, 'c': 8.667201714, 'b': 216.3327983}),
 ('triangular', {'a': 0, 'c': 0, 'b': 225}),
 ('triangular', {'a': 75.50510257, 'c': 100, 'b': 124.4948974}),
 ('triangular', {'a': 51.01020514, 'c': 100, 'b': 148.9897949}),
 ('triangular', {'a': 26.51530772, 'c': 100, 'b': 173.4846923}),
 ('triangular', {'a': 0, 'c': 63.39745962, 'b': 236.6025404}),
 ('triangular', {'a': 0, 'c': 0, 'b': 300}),
 ('triangular', {'a': 100.5051026, 'c': 125, 'b': 149.4948974}),
 ('triangular', {'a': 76.01020514, 'c': 125, 'b': 173.9897949}),
 ('triangular', {'a': 51.51530772, 'c': 125, 'b': 198.4846923}),
 ('triangular', {'a': 2.525512861, 'c': 125, 'b': 247.4744871}),
 ('triangular', {'a': 0, 'c': 0, 'b': 375}),
 ('triangular', {'a': 125.5051026, 'c': 150, 'b': 174.4948974}),
 ('triangular', {'a': 101.0102051, 'c': 150, 'b': 198.9897949}),
 ('triangular', {'a': 76.51530772, 'c': 150, 'b': 223.4846923}),
 ('triangular', {'a': 27.52551286, 'c': 150, 'b': 272.4744871}),
 ('triangular', {'a': 0, 'c': 17.33440343, 'b': 432.6655966}),
 ('weibull', {'k': 5.797400066, 'lam': 53.99876557}),
 ('weibull', {'k': 2.695621255, 'lam': 56.22817503}),
 ('weibull', {'k': 1.71708343, 'lam': 56.07564066}),
 ('weibull', {'k': 1, 'lam': 50}),
 ('weibull', {'k': 0.542692561, 'lam': 28.76247774}),
 ('weibull', {'k': 8.966227479, 'lam': 79.21387693}),
 ('weibull', {'k': 4.230528769, 'lam': 82.47949364}),
 ('weibull', {'k': 2.695621255, 'lam': 84.34226255}),
 ('weibull', {'k': 1.530094248, 'lam': 83.27231}),
 ('weibull', {'k': 0.759909494, 'lam': 63.66669132}),
 ('weibull', {'k': 12.15343419, 'lam': 104.3037681}),
 ('weibull', {'k': 5.797400066, 'lam': 107.9975311}),
 ('weibull', {'k': 3.713772366, 'lam': 110.7863867}),
 ('weibull', {'k': 2.101349095, 'lam': 112.906339}),
 ('weibull', {'k': 1, 'lam': 100}),
 ('weibull', {'k': 15.34819948, 'lam': 129.3518902}),
 ('weibull', {'k': 7.378193605, 'lam': 133.2667586}),
 ('weibull', {'k': 4.750558205, 'lam': 136.544914}),
 ('weibull', {'k': 2.695621255, 'lam': 140.5704376}),
 ('weibull', {'k': 1.258249263, 'lam': 134.4083046}),
 ('weibull', {'k': 18.54679366, 'lam': 154.3815327}),
 ('weibull', {'k': 8.966227479, 'lam': 158.4277539}),
 ('weibull', {'k': 5.797400066, 'lam': 161.9962967}),
 ('weibull', {'k': 3.303524837, 'lam': 167.2122472}),
 ('weibull', {'k': 1.530094248, 'lam': 166.54462}),
 ('exponential', {'rate': 0.02}),
 ('exponential', {'rate': 0.013333333}),
 ('exponential', {'rate': 0.01}),
 ('exponential', {'rate': 0.008}),
 ('exponential', {'rate': 0.006666667}),
 ('poisson', {'lam': 50}),
 ('poisson', {'lam': 75}),
 ('poisson', {'lam': 100}),
 ('poisson', {'lam': 125}),
 ('poisson', {'lam': 150})]
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
    dir_name = os.path.dirname(file_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
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
    output_dir = os.path.dirname(os.path.abspath(__file__))

    seen_output_names = set()
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
                test_path = os.path.join(output_dir, f"{dist_tag}_L{L}_c{hc}_{lc}_test.json")
                if test_path in seen_output_names:
                    raise ValueError(f"Duplicate output filename detected: {test_path}")
                seen_output_names.add(test_path)
                save_instances(test_instances, test_path)

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
                train_path = os.path.join(output_dir, f"{dist_tag}_L{L}_c{hc}_{lc}_train.json")
                if train_path in seen_output_names:
                    raise ValueError(f"Duplicate output filename detected: {train_path}")
                seen_output_names.add(train_path)
                save_instances(train_instances, train_path)
