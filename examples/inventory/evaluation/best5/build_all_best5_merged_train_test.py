#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


DATASET_RE = re.compile(r"^(?P<dist>.+)_L(?P<L>\d+)_p(?P<p>\d+)_(?P<mode>train|test)$")


def p_to_float(token: str) -> float:
    return float(token.replace("p", ".").replace("m", "-"))


def parse_params(dist_tag: str) -> Tuple[str, Dict[str, float]]:
    parts = dist_tag.split("_")
    family = parts[0]
    params: Dict[str, float] = {}
    keys = ["mlog", "lam", "pi", "th", "xm", "sd", "mu", "M", "a", "b", "c", "r", "n", "p", "L", "H", "k", "s"]
    for tok in parts[1:]:
        for k in keys:
            if tok.startswith(k):
                raw = tok[len(k):]
                params[k] = p_to_float(raw)
                break
    return family, params


def demand_moments(family: str, params: Dict[str, float]) -> Tuple[float, float]:
    if family == "beta":
        a, b, m = params["a"], params["b"], params["M"]
        mean = m * a / (a + b)
        var = (m * m) * (a * b) / (((a + b) ** 2) * (a + b + 1.0))
        return mean, var

    if family == "binom":
        n, p = params["n"], params["p"]
        return n * p, n * p * (1.0 - p)

    if family == "cunif":
        a, b = params["a"], params["b"]
        return (a + b) / 2.0, ((b - a) ** 2) / 12.0

    if family == "dunif":
        l, h = params["L"], params["H"]
        mean = (l + h) / 2.0
        var = (((h - l + 1.0) ** 2) - 1.0) / 12.0
        return mean, var

    if family == "gamma":
        k, theta = params["k"], params["th"]
        return k * theta, k * (theta ** 2)

    if family == "geom":
        p = params["p"]
        return (1.0 - p) / p, (1.0 - p) / (p ** 2)

    if family == "logn":
        mu_log, sigma = params["mlog"], params["s"]
        mean = math.exp(mu_log + (sigma ** 2) / 2.0)
        var = (math.exp(sigma ** 2) - 1.0) * math.exp(2.0 * mu_log + sigma ** 2)
        return mean, var

    if family == "negbin":
        r, p = params["r"], params["p"]
        return r * (1.0 - p) / p, r * (1.0 - p) / (p ** 2)

    if family == "normal":
        mu, sigma = params["mu"], params["sd"]
        return mu, sigma ** 2

    if family == "pareto":
        alpha, xm = params["a"], params["xm"]
        mean = alpha * xm / (alpha - 1.0)
        if alpha <= 2.0:
            return mean, float("inf")
        var = alpha * (xm ** 2) / (((alpha - 1.0) ** 2) * (alpha - 2.0))
        return mean, var

    if family == "tri":
        a, c, b = params["a"], params["c"], params["b"]
        mean = (a + b + c) / 3.0
        var = (a * a + b * b + c * c - a * b - a * c - b * c) / 18.0
        return mean, var

    if family == "weib":
        k, lam = params["k"], params["lam"]
        g1 = math.gamma(1.0 + 1.0 / k)
        g2 = math.gamma(1.0 + 2.0 / k)
        mean = lam * g1
        var = (lam ** 2) * (g2 - g1 ** 2)
        return mean, var

    if family == "zinb":
        pi0, r, p = params["pi"], params["r"], params["p"]
        mu_nb = r * (1.0 - p) / p
        var_nb = r * (1.0 - p) / (p ** 2)
        mean = (1.0 - pi0) * mu_nb
        var = (1.0 - pi0) * var_nb + pi0 * (1.0 - pi0) * (mu_nb ** 2)
        return mean, var

    raise ValueError(f"Unsupported distribution family: {family}")


def fmt_num(x: float) -> str:
    if math.isinf(x):
        return "inf"
    return f"{x:.10g}"


def pick_col(columns: Iterable[str], prefix: str) -> str:
    matches = [c for c in columns if c.startswith(prefix)]
    if not matches:
        raise KeyError(f"Missing column starting with '{prefix}'")
    if len(matches) > 1:
        raise KeyError(f"Ambiguous columns for '{prefix}': {matches}")
    return matches[0]


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    in_dir = base_dir / "with_basestock"
    out_path = base_dir / "all_best5_merged_train_test.csv"

    input_files = sorted(in_dir.glob("cost_matrix_L*_p*.csv"))
    if not input_files:
        raise FileNotFoundError(f"No input cost matrix files in {in_dir}")

    agg: Dict[Tuple[str, str, str, str, str, str], Dict[str, float]] = {}

    for f in input_files:
        with f.open(newline="", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            if not reader.fieldnames:
                continue
            fieldnames = list(reader.fieldnames)
            exp_col = pick_col(fieldnames, "exponential_")
            normal_col = pick_col(fieldnames, "normal_")
            poisson_col = pick_col(fieldnames, "poisson_")
            base_col = "avg_cost_basestock"
            if base_col not in fieldnames:
                raise KeyError(f"Missing '{base_col}' in {f}")

            for r in reader:
                dataset = (r.get("dataset") or "").strip()
                m = DATASET_RE.match(dataset)
                if not m:
                    raise ValueError(f"Unexpected dataset format: {dataset}")

                dist_tag = m.group("dist")
                lead_time = int(m.group("L"))
                cost_ratio = int(m.group("p"))
                mode = m.group("mode")

                family, params = parse_params(dist_tag)
                mean, var = demand_moments(family, params)

                key = (
                    family,
                    fmt_num(mean),
                    fmt_num(var),
                    str(lead_time),
                    str(cost_ratio),
                    mode,
                )
                if key not in agg:
                    agg[key] = {
                        "n": 0.0,
                        "policy_exponential": 0.0,
                        "policy_normal": 0.0,
                        "policy_poisson": 0.0,
                        "policy_base_stock": 0.0,
                    }
                agg[key]["n"] += 1.0
                agg[key]["policy_exponential"] += float(r.get(exp_col) or "nan")
                agg[key]["policy_normal"] += float(r.get(normal_col) or "nan")
                agg[key]["policy_poisson"] += float(r.get(poisson_col) or "nan")
                agg[key]["policy_base_stock"] += float(r.get(base_col) or "nan")

    rows: List[Dict[str, str]] = []
    for key, v in agg.items():
        n = v["n"]
        rows.append(
            {
                "distribution": key[0],
                "demand_mean": key[1],
                "demand_variance": key[2],
                "lead_time": key[3],
                "cost_ratio": key[4],
                "mode": key[5],
                "exponential_L6_c1_2": fmt_num(v["policy_exponential"] / n),
                "normal_std30_L6_c1_2": fmt_num(v["policy_normal"] / n),
                "poisson_L6_c1_2": fmt_num(v["policy_poisson"] / n),
                "avg_cost_basestock": fmt_num(v["policy_base_stock"] / n),
            }
        )

    def sort_key(x: Dict[str, str]):
        def maybe_inf(s: str) -> float:
            if s == "inf":
                return float("inf")
            return float(s)

        return (
            x["distribution"],
            maybe_inf(x["demand_mean"]),
            maybe_inf(x["demand_variance"]),
            int(x["lead_time"]),
            int(x["cost_ratio"]),
            0 if x["mode"] == "train" else 1,
        )

    rows.sort(key=sort_key)

    out_cols = [
        "distribution",
        "demand_mean",
        "demand_variance",
        "lead_time",
        "cost_ratio",
        "mode",
        "exponential_L6_c1_2",
        "normal_std30_L6_c1_2",
        "poisson_L6_c1_2",
        "avg_cost_basestock",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=out_cols)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
