"""Shared, strict inventory environment; never loads data on import.

Finite-horizon demand arrays contain selling demand ONLY. The simulator prepends
L zero-demand planning periods, starts with zero inventory and empty pipeline,
and charges costs only during selling. A policy receives post-arrival inventory
and a copy of the L-1 outstanding orders, before the current demand is revealed.

This callable interface does not prove stationarity or provide a security
sandbox. Generated programs must be isolated and checked by the outer runner.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from numbers import Integral, Real
from pathlib import Path
import re
from time import perf_counter
from typing import Callable, Literal

import numpy as np


DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "evaluation" / "data"
CORE_SCENARIO_IDS = (
    "poisson_L6_c1_2",
    "normal_std30_L6_c1_2",
    "exponential_L6_c1_2",
)
_SCENARIO_PATTERN = re.compile(
    r"(?P<family>poisson|exponential|normal_std(?P<std>\d+))"
    r"_L(?P<lead_time>\d+)_c(?P<holding>\d+)_(?P<lost>\d+)"
)
Policy = Callable[..., Real]


def _positive_integer(value: int, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    distribution: Literal["poisson", "normal", "exponential"]
    lead_time: int
    holding_cost: float = 1.0
    lost_sales_cost: float = 2.0
    mean_demand: float = 100.0
    std_normal: float | None = None
    horizon: int = 50

    def __post_init__(self) -> None:
        if not self.scenario_id:
            raise ValueError("scenario_id must be nonempty")
        if self.distribution not in {"poisson", "normal", "exponential"}:
            raise ValueError(f"Unsupported distribution: {self.distribution}")
        _positive_integer(self.lead_time, "lead_time")
        _positive_integer(self.horizon, "horizon")
        for name in ("holding_cost", "lost_sales_cost", "mean_demand"):
            value = getattr(self, name)
            if not isinstance(value, Real) or not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative")
        if self.distribution == "exponential" and self.mean_demand <= 0:
            raise ValueError("Exponential mean_demand must be positive")
        if self.distribution == "normal":
            if (
                not isinstance(self.std_normal, Real)
                or not math.isfinite(self.std_normal)
                or self.std_normal < 0
            ):
                raise ValueError("Normal demand requires finite nonnegative std_normal")
        elif self.std_normal is not None:
            raise ValueError("std_normal applies only to normal demand")

    @classmethod
    def from_id(cls, scenario_id: str) -> "Scenario":
        """Parse the existing mean-100 dataset naming convention."""
        match = _SCENARIO_PATTERN.fullmatch(scenario_id)
        if match is None:
            raise ValueError(f"Invalid scenario ID: {scenario_id}")
        values = match.groupdict()
        return cls(
            scenario_id=scenario_id,
            distribution="normal" if values["std"] else values["family"],
            lead_time=int(values["lead_time"]),
            holding_cost=float(values["holding"]),
            lost_sales_cost=float(values["lost"]),
            std_normal=float(values["std"]) if values["std"] else None,
        )

    def to_params(self) -> dict:
        """Return public design parameters, with no demand samples or filenames."""
        return asdict(self)


def discover_scenarios(data_dir: Path | str | None = None) -> tuple[Scenario, ...]:
    """Discover paired train/test files by name without opening demand data."""
    directory = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    if not directory.is_dir():
        raise FileNotFoundError(directory)
    found: dict[str, set[str]] = {}
    for split in ("train", "test"):
        suffix = f"_{split}.json"
        for path in directory.glob(f"*{suffix}"):
            scenario_id = path.name.removesuffix(suffix)
            if _SCENARIO_PATTERN.fullmatch(scenario_id):
                found.setdefault(scenario_id, set()).add(split)
    if not found:
        raise ValueError(f"No supported scenario data found in {directory}")
    incomplete = [key for key, splits in found.items() if len(splits) != 2]
    if incomplete:
        raise ValueError(f"Missing train/test pair for: {', '.join(sorted(incomplete))}")
    return tuple(Scenario.from_id(key) for key in sorted(found))


def sample_demands(
    scenario: Scenario,
    n_paths: int,
    *,
    seed: int,
    horizon: int | None = None,
) -> np.ndarray:
    """Generate reproducible selling demand using NumPy's local PCG64 RNG.

    Normal draws are clipped at zero, then rounded with np.rint (ties to even).
    Exponential draws are rounded with the same rule. The nominal mean refers
    to the distribution before clipping/rounding, as in the existing generator.
    """
    n_paths = _positive_integer(n_paths, "n_paths")
    periods = _positive_integer(scenario.horizon if horizon is None else horizon, "horizon")
    if isinstance(seed, (bool, np.bool_)) or not isinstance(seed, Integral) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    rng = np.random.default_rng(int(seed))
    size = (n_paths, periods)
    if scenario.distribution == "poisson":
        return rng.poisson(scenario.mean_demand, size=size).astype(np.int64)
    if scenario.distribution == "normal":
        draws = rng.normal(scenario.mean_demand, scenario.std_normal, size=size)
        return np.rint(np.maximum(draws, 0.0)).astype(np.int64)
    draws = rng.exponential(scenario.mean_demand, size=size)
    return np.rint(draws).astype(np.int64)


def _validate_demands(demands: np.ndarray) -> np.ndarray:
    raw = np.asarray(demands)
    if np.iscomplexobj(raw):
        raise ValueError("Demands must be real")
    try:
        array = np.array(raw, dtype=float, copy=True)
    except (TypeError, ValueError) as exc:
        raise ValueError("Demands must be a rectangular numeric array") from exc
    if array.ndim == 1:
        array = array.reshape(1, -1)
    if array.ndim != 2 or not array.shape[0] or not array.shape[1]:
        raise ValueError("Demands must have shape (n_paths, n_periods) with nonzero dimensions")
    if not np.isfinite(array).all() or (array < 0).any():
        raise ValueError("Demands must be finite and nonnegative")
    array.setflags(write=False)
    return array


def load_demands(
    scenario: Scenario,
    split: Literal["train", "test"],
    *,
    n_paths: int | None = None,
    data_dir: Path | str | None = None,
) -> np.ndarray:
    """Explicitly load a split; the generation process must never call for test.

    Metadata and exact horizon are validated rather than silently truncating or
    padding a file that may already contain planning demands. Files are read-only.
    """
    if split not in {"train", "test"}:
        raise ValueError("split must be 'train' or 'test'")
    if scenario.mean_demand != 100:
        raise ValueError("Existing dataset IDs specify nominal mean 100")
    directory = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    path = directory / f"{scenario.scenario_id}_{split}.json"
    with path.open(encoding="utf-8") as handle:
        instances = json.load(handle)
    if not isinstance(instances, list) or not instances:
        raise ValueError(f"Expected a nonempty list of instances in {path}")
    if n_paths is not None:
        n_paths = _positive_integer(n_paths, "n_paths")
        if n_paths > len(instances):
            raise ValueError(f"Requested {n_paths} paths but {path.name} has {len(instances)}")
        instances = instances[:n_paths]
    for index, instance in enumerate(instances):
        expected = {
            "initial_inventory": 0,
            "lead_time": scenario.lead_time,
            "holding_cost": scenario.holding_cost,
            "lost_sales_cost": scenario.lost_sales_cost,
            "distribution": scenario.distribution,
            "num_periods": scenario.horizon,
            "std_normal": scenario.std_normal,
        }
        for key, value in expected.items():
            if instance.get(key) != value:
                raise ValueError(f"{path.name}, path {index}: {key} != {value!r}")
        if len(instance.get("demand", [])) != scenario.horizon:
            raise ValueError(f"{path.name}, path {index}: incorrect selling horizon")
    return _validate_demands([instance["demand"] for instance in instances])


class InvalidPolicyError(ValueError):
    """The policy raised an exception or returned an invalid action."""


def adapt_order(order: Callable[[float, list[float]], Real]) -> Policy:
    """Adapt an order(on_hand, pipeline) closure to the named public interface."""
    if not callable(order):
        raise TypeError("order must be callable")

    def compute_order_amount(*, on_hand_inventory: float, pipeline_orders: list[float]) -> Real:
        return order(on_hand_inventory, pipeline_orders)

    return compute_order_amount


@dataclass(frozen=True)
class SimulationResult:
    """Per-path totals; every array has shape (n_paths,)."""

    total_cost: np.ndarray
    holding_cost: np.ndarray
    lost_sales_cost: np.ndarray
    demand_units: np.ndarray
    sales_units: np.ndarray
    lost_units: np.ndarray
    service_level: np.ndarray
    policy_seconds: np.ndarray
    periods_scored: int
    periods_simulated: int
    mode: str
    integer_orders: bool

    def summary(self) -> dict:
        """Mean costs and both path-mean and demand-weighted fill rates."""
        demand = float(self.demand_units.sum())
        return {
            "n_paths": len(self.total_cost),
            "periods_scored": self.periods_scored,
            "periods_simulated": self.periods_simulated,
            "mode": self.mode,
            "integer_orders": self.integer_orders,
            "mean_total_cost": float(self.total_cost.mean()),
            "mean_cost_per_period": float(self.total_cost.mean() / self.periods_scored),
            "mean_holding_cost": float(self.holding_cost.mean()),
            "mean_lost_sales_cost": float(self.lost_sales_cost.mean()),
            "mean_service_level": float(self.service_level.mean()),
            "demand_weighted_service_level": float(self.sales_units.sum() / demand) if demand else 1.0,
            "total_policy_seconds": float(self.policy_seconds.sum()),
        }


def simulate_policy(
    policy: Policy,
    scenario: Scenario,
    demands: np.ndarray,
    *,
    mode: Literal["finite", "long_run"] = "finite",
    burn_in: int = 0,
    integer_orders: bool = False,
) -> SimulationResult:
    """Evaluate a frozen stationary policy on shared demand paths.

    ``finite`` requires scenario.horizon selling columns and prepends L zeros.
    ``long_run`` starts from zero and uses the supplied demands immediately,
    without zero-demand planning. Its first burn_in stochastic periods affect
    state but are excluded from every reported cost and service metric.

    Orders are uncapped, finite, nonnegative real scalars. Invalid outputs and
    exceptions stop evaluation; they are never replaced with zero. If requested,
    integer sensitivity uses np.rint (ties to even) after validating the order.
    Policies receive only the two documented keywords and a defensive pipeline
    copy. Call timing is observational and never passed to the policy.
    """
    if not callable(policy):
        raise TypeError("policy must be callable")
    if mode not in {"finite", "long_run"}:
        raise ValueError("mode must be 'finite' or 'long_run'")
    if isinstance(burn_in, (bool, np.bool_)) or not isinstance(burn_in, Integral) or burn_in < 0:
        raise ValueError("burn_in must be a nonnegative integer")
    array = _validate_demands(demands)
    n_paths, selling_periods = array.shape
    if mode == "finite":
        if burn_in:
            raise ValueError("Finite evaluation does not use stochastic burn-in")
        if selling_periods != scenario.horizon:
            raise ValueError(f"Expected {scenario.horizon} selling periods, got {selling_periods}")
        planning = scenario.lead_time
        score_start = planning
    else:
        if burn_in >= selling_periods:
            raise ValueError("burn_in must leave at least one scored period")
        planning = 0
        score_start = int(burn_in)
    periods_simulated = selling_periods + planning
    periods_scored = periods_simulated - score_start
    holding = np.zeros(n_paths)
    lost_cost = np.zeros(n_paths)
    demand_total = np.zeros(n_paths)
    sales_total = np.zeros(n_paths)
    lost_total = np.zeros(n_paths)
    policy_seconds = np.zeros(n_paths)

    for path_index, demand_path in enumerate(array):
        on_hand = 0.0
        pipeline = [0.0] * scenario.lead_time
        for period in range(periods_simulated):
            on_hand += pipeline.pop(0)
            if not math.isfinite(on_hand):
                raise InvalidPolicyError(f"Inventory overflow at path {path_index}, period {period}")
            started = perf_counter()
            try:
                action = policy(on_hand_inventory=on_hand, pipeline_orders=pipeline.copy())
            except Exception as exc:
                raise InvalidPolicyError(
                    f"Policy raised {type(exc).__name__} at path {path_index}, period {period}"
                ) from exc
            finally:
                policy_seconds[path_index] += perf_counter() - started
            if isinstance(action, (bool, np.bool_)) or not isinstance(action, Real):
                raise InvalidPolicyError(
                    f"Order must be a finite nonnegative real scalar at path {path_index}, period {period}"
                )
            try:
                order = float(action)
            except (OverflowError, TypeError, ValueError) as exc:
                raise InvalidPolicyError(
                    f"Order cannot be represented as a finite float at path {path_index}, period {period}"
                ) from exc
            if not math.isfinite(order) or order < 0:
                raise InvalidPolicyError(
                    f"Order must be a finite nonnegative real scalar at path {path_index}, period {period}"
                )
            if integer_orders:
                order = float(np.rint(order))
            pipeline.append(order)
            demand = 0.0 if period < planning else float(demand_path[period - planning])
            sales = min(on_hand, demand)
            lost = demand - sales
            on_hand -= sales
            if period >= score_start:
                holding[path_index] += scenario.holding_cost * on_hand
                lost_cost[path_index] += scenario.lost_sales_cost * lost
                demand_total[path_index] += demand
                sales_total[path_index] += sales
                lost_total[path_index] += lost
                if not math.isfinite(holding[path_index]) or not math.isfinite(lost_cost[path_index]):
                    raise InvalidPolicyError(f"Cost overflow at path {path_index}, period {period}")

    total_cost = holding + lost_cost
    if not np.isfinite(total_cost).all():
        raise InvalidPolicyError("Total cost overflow")
    service = np.divide(sales_total, demand_total, out=np.ones(n_paths), where=demand_total > 0)
    arrays = (total_cost, holding, lost_cost, demand_total, sales_total, lost_total, service, policy_seconds)
    for values in arrays:
        values.setflags(write=False)
    return SimulationResult(
        total_cost=total_cost,
        holding_cost=holding,
        lost_sales_cost=lost_cost,
        demand_units=demand_total,
        sales_units=sales_total,
        lost_units=lost_total,
        service_level=service,
        policy_seconds=policy_seconds,
        periods_scored=periods_scored,
        periods_simulated=periods_simulated,
        mode=mode,
        integer_orders=integer_orders,
    )
