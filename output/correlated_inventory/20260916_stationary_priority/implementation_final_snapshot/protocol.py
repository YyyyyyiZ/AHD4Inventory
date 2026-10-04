"""Prospective experiment configuration, frozen before holdout evaluation."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys

from .api_client import atomic_json, MODEL

REPO = Path(__file__).resolve().parents[3]
DEFAULT_RUN = REPO / "output/correlated_inventory/20260916_stationary_priority"
HORIZONS = (50, 100, 200, 500)
PROTOCOL = {
    "protocol_id": "stationary-correlated-exp100-v1",
    "model": MODEL,
    "api_budget_usd": 20.0,
    "demand_mean": 100.0,
    "holding_cost": 1.0,
    "lost_sales_cost": 2.0,
    "demand_observation": "full past realized demand, including unmet demand, available equally to all policies",
    "policy_interface": "compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time)",
    "timing": "old arrivals -> observe current lead-time quote -> order -> current demand -> holding/lost-sales cost",
    "random_lead": "iid uniform on {3,9}, quote known before ordering, overtaking allowed, sampled by calendar period even for zero orders",
    "pipeline": "old arrivals in future periods 1 through max_lead-1; aggregate by arrival date",
    "policy_information": "generator parameters known, current/future demand and future lead quotes unavailable, no horizon/time index",
    "train_paths": 50,
    "validation_paths": 128,
    "test_paths": 1000,
    "tape_periods": 1000,
    "training_horizon": 200,
    "burn_in": 500,
    "horizons": list(HORIZONS),
    "evaluation_modes": {"steady": 500, "cold_start": 0},
    "initial_inventory": 0.0,
    "initial_pipeline": "empty",
    "steady_caveat": "finite stochastic burn-in approximates stationary inventory; demand itself starts exactly stationary",
    "cold_start": "actual stationary demand from period zero, no free zero-demand planning periods",
    "seed_root": 2026091601,
    "splits": ["train", "validation", "test"],
    "same_paths_across_horizons": "nested prefixes of a single maximum-length tape; no resampling when horizon changes",
    "selection": "optimizer and EOH parent selection use train only; one final candidate per independent run frozen before holdout",
    "holdout_reporting": "all scenarios and all runs, no test-driven selection of favorable environments or policies",
    "evolution": {"operator": "m2", "population": 10, "generations": 10, "repetitions": 3,
                  "optimizer": "original ScipyOptimizer L-BFGS-B", "maxiter": 15,
                  "max_opt_params": 4, "feedback": "compact train-only demand summary and processed scored-window feedback",
                  "initial_seed": "base-stock policy", "selection_parent": "best training policy"},
    "primary_runs": 18,
    "horizon_refit_extension": {"scenario": "positive AR latent rho=0.8, fixed lead6",
                                "horizons": [50, 100, 500], "repetitions": 3,
                                "priority": "after all 18 primary runs, within global API budget"},
    "baseline_families": ["constant_order", "base_stock", "capped_base_stock", "forecast_capped_base_stock",
                          "conditional_PIL", "adaptive_conditional_PIL", "PIL_COP_continuation_for_random_lead"],
    "PIL_label": "projected inventory level, an adaptation used for the requested projected base-stock comparator; random-lead continuation assumptions disclosed",
    "baseline_tuning": "train only, deterministic conditional QMC draws, train-only integration-accuracy checks",
    "metrics": ["cost_per_period", "holding_per_period", "lost_units_per_period", "fill_rate", "orders_per_period"],
    "uncertainty": "paired whole-path bootstrap; paths independent, within-path periods and horizon prefixes dependent",
    "no_guaranteed_winner": True,
    "sources": {
        "gaussian_copula": "https://eml.berkeley.edu/~powell/e242_sp04/chen.pdf",
        "projected_inventory_level": "https://arxiv.org/html/2101.07519v4#S3",
        "random_lead_overtaking": "https://arxiv.org/abs/1801.02646",
        "provider_price_cap": "https://openrouter.ai/docs/guides/routing/provider-selection",
    },
}


def freeze_protocol(run_dir=DEFAULT_RUN):
    run_dir = Path(run_dir)
    target = run_dir / "protocol.json"
    if target.exists():
        existing = json.loads(target.read_text())
        if existing["configuration"] != PROTOCOL:
            raise ValueError("Frozen protocol mismatch; record an explicit amendment instead of overwriting")
        return existing
    import numpy, scipy, numba
    record = dict(created_utc=datetime.now(timezone.utc).isoformat(), configuration=PROTOCOL,
                  runtime={"python": sys.version, "numpy": numpy.__version__, "scipy": scipy.__version__,
                           "numba": numba.__version__, "platform": platform.platform()})
    atomic_json(target, record)
    return record


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot_sources(run_dir=DEFAULT_RUN, name="source_snapshot"):
    import shutil
    destination = Path(run_dir) / name
    destination.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for source in sorted(Path(__file__).parent.glob("*.py")):
        dest = destination / source.name
        if dest.exists() and dest.read_bytes() != source.read_bytes():
            raise ValueError("Snapshot is immutable; choose a new snapshot name")
        shutil.copy2(source, dest)
        hashes[source.name] = file_sha256(dest)
    atomic_json(destination / "sha256.json", hashes)
    return hashes


if __name__ == "__main__":
    freeze_protocol()
    print(DEFAULT_RUN / "protocol.json")
