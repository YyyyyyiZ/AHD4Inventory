"""Stationary, marginal-matched demand and exogenous calendar lead-time tapes.

Only realized demand, calendar lead times, and one prehistory demand are stored.
Latent states are never part of the policy interface. All six specifications have
the exact continuous Exponential(mean=100) one-period marginal; ``rho_latent``
is the Gaussian AR coefficient, not Pearson correlation of demand.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from numbers import Integral
from pathlib import Path

import numpy as np
from scipy.signal import lfilter
from scipy.special import log_ndtr


DATA_VERSION = "stationary-exponential-tapes-v1"
ARRAY_KEYS = ("demands", "lead_times", "initial_last_demand")


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    demand_process: str = "iid"
    rho_latent: float = 0.0
    regime_p_stay: float = 0.95
    lead_time_values: tuple[int, ...] = (6,)
    lead_time_probabilities: tuple[float, ...] = (1.0,)
    mean_demand: float = 100.0
    holding_cost: float = 1.0
    lost_sales_cost: float = 2.0

    def __post_init__(self):
        object.__setattr__(self, "lead_time_values", tuple(self.lead_time_values))
        object.__setattr__(self, "lead_time_probabilities", tuple(self.lead_time_probabilities))
        if not self.scenario_id or self.demand_process not in {"iid", "ar1", "regime"}:
            raise ValueError("Invalid scenario ID or demand process")
        if not math.isfinite(self.rho_latent) or not -1 < self.rho_latent < 1:
            raise ValueError("rho_latent must be in (-1, 1)")
        if self.demand_process != "ar1" and self.rho_latent != 0:
            raise ValueError("Only AR1 scenarios may specify nonzero rho_latent")
        if not math.isfinite(self.regime_p_stay) or not 0 < self.regime_p_stay < 1:
            raise ValueError("regime_p_stay must be in (0, 1)")
        if not self.lead_time_values or any(
            isinstance(x, (bool, np.bool_)) or not isinstance(x, Integral) or x < 1
            for x in self.lead_time_values
        ) or len(set(self.lead_time_values)) != len(self.lead_time_values):
            raise ValueError("Lead-time values must be distinct positive integers")
        if len(self.lead_time_values) != len(self.lead_time_probabilities) or any(
            not math.isfinite(x) or x <= 0 for x in self.lead_time_probabilities
        ) or not math.isclose(sum(self.lead_time_probabilities), 1.0, abs_tol=1e-12):
            raise ValueError("Lead-time probabilities must be positive and sum to one")
        for name in ("mean_demand", "holding_cost", "lost_sales_cost"):
            x = getattr(self, name)
            if not math.isfinite(x) or x < 0 or (name == "mean_demand" and x == 0):
                raise ValueError(f"Invalid {name}")

    @property
    def max_lead_time(self) -> int:
        return max(self.lead_time_values)

    @property
    def mean_lead_time(self) -> float:
        return float(sum(x * p for x, p in zip(self.lead_time_values, self.lead_time_probabilities)))

    def to_dict(self) -> dict:
        return asdict(self)


def scenario_specs() -> tuple[Scenario, ...]:
    """The preregistered four fixed-lead and two random-lead environments."""
    return (
        Scenario("exp_iid_fixed6"),
        Scenario("exp_ar_pos08_fixed6", "ar1", rho_latent=0.8),
        Scenario("exp_ar_neg06_fixed6", "ar1", rho_latent=-0.6),
        Scenario("exp_regime095_fixed6", "regime"),
        Scenario("exp_iid_random3_9", lead_time_values=(3, 9), lead_time_probabilities=(0.5, 0.5)),
        Scenario("exp_regime095_random3_9", "regime", lead_time_values=(3, 9), lead_time_probabilities=(0.5, 0.5)),
    )


def _positive_int(value, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def _arrays_hash(tapes: dict) -> str:
    digest = hashlib.sha256()
    for key, dtype in (("demands", "<f8"), ("lead_times", "<i8"), ("initial_last_demand", "<f8")):
        array = np.ascontiguousarray(tapes[key], dtype=dtype)
        digest.update(key.encode())
        digest.update(json.dumps(array.shape).encode())
        digest.update(array.tobytes())
    return digest.hexdigest()


def validate_tapes(tapes: dict, scenario: Scenario | None = None) -> dict:
    """Validate, normalize dtypes, and freeze arrays; no latent information."""
    if not isinstance(tapes, dict) or not set(ARRAY_KEYS).issubset(tapes):
        raise ValueError("Tape dictionary is missing required arrays")
    raw_d = np.asarray(tapes["demands"])
    raw_l = np.asarray(tapes["lead_times"])
    raw_i = np.asarray(tapes["initial_last_demand"])
    if any(np.iscomplexobj(x) for x in (raw_d, raw_l, raw_i)):
        raise ValueError("Tape values must be real")
    demands = np.array(raw_d, dtype=np.float64, order="C", copy=True)
    initial = np.array(raw_i, dtype=np.float64, order="C", copy=True)
    if demands.ndim != 2 or min(demands.shape) < 1 or initial.shape != (len(demands),):
        raise ValueError("Expected demands[N,T] and initial_last_demand[N]")
    if raw_l.shape != demands.shape or raw_l.dtype.kind not in "iu" or raw_l.dtype.kind == "b":
        raise ValueError("lead_times must be an integer array matching demands")
    if not np.isfinite(demands).all() or not np.isfinite(initial).all() or (demands < 0).any() or (initial < 0).any():
        raise ValueError("Demand must be finite and nonnegative")
    if (raw_l < 1).any() or (raw_l > np.iinfo(np.int64).max).any():
        raise ValueError("Lead times must be positive int64 values")
    leads = np.array(raw_l, dtype=np.int64, order="C", copy=True)
    if scenario is not None and not np.isin(leads, scenario.lead_time_values).all():
        raise ValueError("Lead times do not match scenario support")
    metadata = dict(tapes.get("metadata", {}))
    if scenario is not None and "scenario" in metadata and Scenario(**metadata["scenario"]) != scenario:
        raise ValueError("Tape scenario metadata mismatch")
    normalized = {"demands": demands, "lead_times": leads, "initial_last_demand": initial, "metadata": metadata}
    expected = metadata.get("arrays_sha256")
    if expected is not None and expected != _arrays_hash(normalized):
        raise ValueError("Tape array hash mismatch")
    for array in (demands, leads, initial):
        array.setflags(write=False)
    return normalized


def generate_tapes(spec: Scenario, n_paths: int, seed: int, n_periods: int = 1000) -> dict:
    """Generate stationary tapes; both time and path prefixes are seed-stable.

    Per-path independent RNG streams separate demand dynamics, within-regime
    variation, and quoted lead times. Even zero orders consume the same calendar
    lead-time tape. The generator does not know a policy or evaluation horizon.
    """
    n_paths = _positive_int(n_paths, "n_paths")
    n_periods = _positive_int(n_periods, "n_periods")
    if isinstance(seed, (bool, np.bool_)) or not isinstance(seed, Integral) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    demands = np.empty((n_paths, n_periods), dtype=np.float64)
    initial = np.empty(n_paths, dtype=np.float64)
    leads = np.empty((n_paths, n_periods), dtype=np.int64)
    for index, path_seed in enumerate(np.random.SeedSequence(int(seed)).spawn(n_paths)):
        state_seed, within_seed, lead_seed = path_seed.spawn(3)
        state_rng, within_rng, lead_rng = (np.random.default_rng(x) for x in (state_seed, within_seed, lead_seed))
        if spec.demand_process in {"iid", "ar1"}:
            rho = spec.rho_latent if spec.demand_process == "ar1" else 0.0
            z0 = state_rng.standard_normal()
            noise = state_rng.standard_normal(n_periods)
            z, _ = lfilter([math.sqrt(1.0 - rho * rho)], [1.0, -rho], noise, zi=[rho * z0])
            initial[index] = -spec.mean_demand * log_ndtr(-z0)
            demands[index] = -spec.mean_demand * log_ndtr(-z)
        else:
            s0 = int(state_rng.integers(0, 2))
            flips = state_rng.random(n_periods) >= spec.regime_p_stay
            states = (s0 + np.cumsum(flips, dtype=np.int64)) % 2
            v0 = within_rng.random()
            v = within_rng.random(n_periods)
            initial[index] = -spec.mean_demand * math.log1p(-(s0 + v0) / 2.0)
            demands[index] = -spec.mean_demand * np.log1p(-(states + v) / 2.0)
        if len(spec.lead_time_values) == 1:
            leads[index] = spec.lead_time_values[0]
        else:
            # One uniform per calendar period, independent of order placement.
            choices = np.searchsorted(np.cumsum(spec.lead_time_probabilities), lead_rng.random(n_periods), side="right")
            leads[index] = np.asarray(spec.lead_time_values, dtype=np.int64)[choices]
    result = {"demands": demands, "lead_times": leads, "initial_last_demand": initial}
    result["metadata"] = {"version": DATA_VERSION, "scenario": spec.to_dict(), "seed": int(seed),
                          "n_paths": n_paths, "n_periods": n_periods,
                          "initialization": "invariant latent distribution; one observed demand before t=0",
                          "marginal": "continuous Exponential(mean_demand)",
                          "rho_definition": "latent Gaussian AR(1) coefficient, not demand Pearson ACF",
                          "arrays_sha256": _arrays_hash(result)}
    return validate_tapes(result, spec)


def save_tapes(path: str | Path, tapes: dict) -> Path:
    normalized = validate_tapes(tapes)
    metadata = dict(normalized["metadata"])
    metadata["arrays_sha256"] = _arrays_hash(normalized)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        np.savez_compressed(handle, **{key: normalized[key] for key in ARRAY_KEYS},
                            metadata_json=np.array(json.dumps(metadata, sort_keys=True)))
    return destination


def load_tapes(path: str | Path, scenario: Scenario | None = None) -> dict:
    with np.load(Path(path), allow_pickle=False) as data:
        if set(data.files) != set(ARRAY_KEYS) | {"metadata_json"}:
            raise ValueError("Unexpected fields in tape archive")
        result = {key: data[key] for key in ARRAY_KEYS}
        result["metadata"] = json.loads(str(data["metadata_json"].item()))
    return validate_tapes(result, scenario)


def tape_diagnostics(tapes: dict, scenario: Scenario, lags=(1, 2, 5, 10, 20, 50)) -> dict:
    """Descriptive sanity checks only; never select a policy or test scenario."""
    normalized = validate_tapes(tapes, scenario)
    d = normalized["demands"]
    mean, variance = float(d.mean()), float(d.var())
    centered = d - mean
    acf = {str(k): float(np.mean(centered[:, :-k] * centered[:, k:]) / variance)
           for k in lags if isinstance(k, Integral) and 0 < k < d.shape[1] and variance > 0}
    path_means = d.mean(axis=1)
    mean_se = float(path_means.std(ddof=1) / math.sqrt(len(d))) if len(d) > 1 else None
    result = {"scenario_id": scenario.scenario_id, "n_paths": len(d), "n_periods": d.shape[1],
              "marginal_mean": mean, "marginal_std": math.sqrt(variance),
              "expected_mean": scenario.mean_demand, "expected_std": scenario.mean_demand,
              "mean_standard_error_across_independent_paths": mean_se,
              "mean_within_six_path_standard_errors": None if mean_se is None else abs(mean - scenario.mean_demand) <= 6 * mean_se,
              "quantiles": dict(zip(("0.1", "0.5", "0.9", "0.99"), map(float, np.quantile(d, [0.1, 0.5, 0.9, 0.99])))),
              "acf_demand": acf, "rho_latent": scenario.rho_latent,
              "acf_note": "ACF is measured on demand; rho_latent is not demand Pearson correlation",
              "first_period_mean": float(d[:, 0].mean()), "last_period_mean": float(d[:, -1].mean()),
              "initial_last_demand_mean": float(normalized["initial_last_demand"].mean()),
              "lead_time_frequencies": {str(x): float(np.mean(normalized["lead_times"] == x)) for x in scenario.lead_time_values},
              "finite_nonnegative": bool(np.isfinite(d).all() and (d >= 0).all())}
    if scenario.demand_process == "regime":
        labels = d >= scenario.mean_demand * math.log(2.0)
        previous = np.column_stack((normalized["initial_last_demand"] >= scenario.mean_demand * math.log(2.0), labels[:, :-1]))
        result.update(regime_high_fraction=float(labels.mean()), regime_empirical_stay=float(np.mean(labels == previous)),
                      regime_p_stay=scenario.regime_p_stay,
                      regime_mean_duration=1 / (1 - scenario.regime_p_stay),
                      theoretical_acf={str(k): math.log(2.0) ** 2 * (2 * scenario.regime_p_stay - 1) ** k for k in lags if k > 0},
                      regime_formula="S0~Bernoulli(1/2); P(stay)=p; U_t=(S_t+V_t)/2, V_t iid Uniform; D_t=-mu log(1-U_t)")
    return result


diagnostics = tape_diagnostics
