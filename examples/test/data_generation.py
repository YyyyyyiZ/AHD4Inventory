# gen_data_2p_newsvendor.py
import os
import json
import numpy as np
from typing import List, Tuple, Literal

def sample_demands_2p(
    dist: Literal["normal","poisson"],
    size: int,
    normal_params: Tuple[float,float]=(80.0, 5.0),
    poisson_lambda: float = 80.0,
    seed: int = 42
) -> List[Tuple[int,int]]:
    rng = np.random.default_rng(seed)
    if dist == "normal":
        mu, sigma = normal_params
        d1 = np.maximum(0, np.rint(rng.normal(mu, sigma, size=size)).astype(int))
        d2 = np.maximum(0, np.rint(rng.normal(mu, sigma, size=size)).astype(int))
    elif dist == "poisson":
        lam = poisson_lambda
        d1 = rng.poisson(lam=lam, size=size).astype(int)
        d2 = rng.poisson(lam=lam, size=size).astype(int)
    else:
        raise ValueError("dist must be 'normal' or 'poisson'")
    return [(int(d1[i]), int(d2[i])) for i in range(size)]

def main():
    out_dir = "./evaluation/data"
    os.makedirs(out_dir, exist_ok=True)

    # —— 你可以按需修改这些参数 ——
    dist = "poisson"                     # "normal" | "poisson"
    normal_params = (80.0, 5.0)
    poisson_lambda = 80.0
    cost_params = {"h": 1.0, "p": 5.0}  # 两期一致
    train_n = 50
    val_n = 500
    base_seed = 12345

    train = sample_demands_2p(dist, train_n, normal_params, poisson_lambda, seed=base_seed+1)
    val   = sample_demands_2p(dist, val_n, normal_params, poisson_lambda, seed=base_seed+2)

    train_json = {
        "meta": {
            "problem": "2p_newsvendor_lost_sales",
            "distribution": dist,
            "normal_params": list(normal_params),
            "poisson_lambda": poisson_lambda,
            "cost_params": cost_params,
            "seed": base_seed+1,
            "horizon": 2
        },
        "data": [{"d": [d1, d2]} for (d1, d2) in train]
    }
    val_json = {
        "meta": {
            "problem": "2p_newsvendor_lost_sales",
            "distribution": dist,
            "normal_params": list(normal_params),
            "poisson_lambda": poisson_lambda,
            "cost_params": cost_params,
            "seed": base_seed+2,
            "horizon": 2
        },
        "data": [{"d": [d1, d2]} for (d1, d2) in val]
    }

    with open(f"{out_dir}/poisson1_train_80_low.json", "w") as f:
        json.dump(train_json, f, indent=2)
    with open(f"{out_dir}/poisson1_test_80_low.json", "w") as f:
        json.dump(val_json, f, indent=2)

    print("Saved:")
    print(f"  {out_dir}/train_2p_newsvendor.json")
    print(f"  {out_dir}/val_2p_newsvendor.json")

if __name__ == "__main__":
    main()
