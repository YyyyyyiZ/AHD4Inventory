"""Local, network-free checks of stationary tapes and actual event ordering."""

from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile
import unittest

import numpy as np

from .data import Scenario, generate_tapes, load_tapes, save_tapes, scenario_specs, tape_diagnostics, validate_tapes
from .environment import InvalidPolicyError, simulate_callable, simulate_compiled


def _tape(demands, leads, initial=11.0):
    d = np.asarray(demands, dtype=np.float64)
    if d.ndim == 1:
        d = d[None, :]
    l = np.asarray(leads, dtype=np.int64)
    if l.ndim == 1:
        l = np.broadcast_to(l, d.shape).copy()
    return {"demands": d, "lead_times": l, "initial_last_demand": np.full(len(d), initial)}


def _constant_ten(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    return 10.0


def _numba_policy(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    position = on_hand_inventory
    for amount in pipeline_orders:
        position += 0.03 * amount
    return max(0.0, 70.0 + 0.2 * last_demand + quoted_lead_time - 0.15 * position)


class StationaryTapeTests(unittest.TestCase):
    def test_registered_matrix(self):
        specs = scenario_specs()
        self.assertEqual(len(specs), 6)
        self.assertEqual(len({x.scenario_id for x in specs}), 6)
        self.assertEqual(sum(x.max_lead_time == 6 for x in specs), 4)
        for spec in specs:
            self.assertEqual(spec.mean_demand, 100)
            self.assertEqual(spec.mean_lead_time, 6)
            self.assertEqual((spec.holding_cost, spec.lost_sales_cost), (1, 2))

    def test_time_and_path_prefixes_stable_and_no_latent_arrays(self):
        for spec in scenario_specs():
            short = generate_tapes(spec, 3, 914, 20)
            long = generate_tapes(spec, 5, 914, 40)
            self.assertEqual(set(short), {"demands", "lead_times", "initial_last_demand", "metadata"})
            np.testing.assert_array_equal(short["demands"], long["demands"][:3, :20])
            np.testing.assert_array_equal(short["lead_times"], long["lead_times"][:3, :20])
            np.testing.assert_array_equal(short["initial_last_demand"], long["initial_last_demand"][:3])
            self.assertFalse(short["demands"].flags.writeable)

    def test_lead_stream_does_not_change_demand(self):
        specs = scenario_specs()
        for fixed, random in ((specs[0], specs[4]), (specs[3], specs[5])):
            one, two = (generate_tapes(s, 10, 712, 100) for s in (fixed, random))
            np.testing.assert_array_equal(one["demands"], two["demands"])
            np.testing.assert_array_equal(one["initial_last_demand"], two["initial_last_demand"])
            self.assertEqual(set(np.unique(two["lead_times"])), {3, 9})

    def test_invariant_initial_marginals_and_dependency_signs(self):
        # Across-path independent ensembles, not iid tests on correlated periods.
        for spec in scenario_specs()[:4]:
            tapes = generate_tapes(spec, 2000, 6209, 150)
            report = tape_diagnostics(tapes, spec)
            self.assertLess(abs(report["initial_last_demand_mean"] - 100), 7)
            self.assertLess(abs(report["first_period_mean"] - 100), 7)
            self.assertLess(abs(report["last_period_mean"] - 100), 7)
            self.assertLess(abs(report["marginal_mean"] - 100), 4)
            self.assertLess(abs(report["marginal_std"] - 100), 5)
            self.assertLess(abs(report["quantiles"]["0.5"] - 100 * math.log(2)), 4)
            acf = report["acf_demand"]["1"]
            if spec.demand_process == "iid":
                self.assertLess(abs(acf), 0.02)
            elif spec.demand_process == "ar1":
                self.assertGreater(acf, 0.65) if spec.rho_latent > 0 else self.assertLess(acf, -0.3)
            else:
                self.assertLess(abs(report["regime_empirical_stay"] - 0.95), 0.01)
                self.assertLess(abs(report["regime_high_fraction"] - 0.5), 0.025)
                self.assertLess(abs(acf - math.log(2) ** 2 * 0.9), 0.025)

    def test_split_seeds_independent(self):
        spec = scenario_specs()[3]
        a, b = (generate_tapes(spec, 5, seed, 50) for seed in (11, 12))
        self.assertNotEqual(a["metadata"]["arrays_sha256"], b["metadata"]["arrays_sha256"])
        self.assertFalse(np.array_equal(a["demands"], b["demands"]))

    def test_round_trip_and_corruption_detection(self):
        spec = scenario_specs()[4]
        original = generate_tapes(spec, 3, 72, 40)
        with tempfile.TemporaryDirectory() as folder:
            path = save_tapes(Path(folder) / "tapes.npz", original)
            restored = load_tapes(path, spec)
            for name in ("demands", "lead_times", "initial_last_demand"):
                np.testing.assert_array_equal(original[name], restored[name])
            corrupt = {key: np.array(original[key], copy=True) for key in ("demands", "lead_times", "initial_last_demand")}
            corrupt["demands"][0, 0] += 1
            with path.open("wb") as handle:
                np.savez_compressed(handle, **corrupt, metadata_json=np.array(json.dumps(original["metadata"])))
            with self.assertRaisesRegex(ValueError, "hash"):
                load_tapes(path, spec)

    def test_invalid_spec_and_tapes_rejected(self):
        for kwargs in ({"rho_latent": 1}, {"lead_time_values": (0,)},
                       {"lead_time_values": (1, 3), "lead_time_probabilities": (0.2, 0.2)}):
            with self.assertRaises(ValueError):
                Scenario("bad", **kwargs)
        bad = _tape([1, 2], [1, 1])
        bad["lead_times"] = np.ones((1, 2), dtype=float)
        with self.assertRaises(ValueError):
            validate_tapes(bad)
        with self.assertRaises(ValueError):
            validate_tapes(_tape([1, -2], [1, 1]))


class InventoryTimingTests(unittest.TestCase):
    def test_lead_one_hand_calculation_and_no_free_preparation(self):
        spec = Scenario("manual", lead_time_values=(1,))
        result = simulate_callable(_constant_ten, _tape([7, 12, 1], [1, 1, 1]), spec, 3, 0, True)
        self.assertEqual(result["total_cost"][0], 27.0)  # h*9 + p*(7+2)
        self.assertEqual(result["periods_simulated"], 3)
        np.testing.assert_array_equal(result["trace"][0, :, 0], [0, 10, 10])
        np.testing.assert_array_equal(result["trace"][0, :, 8], [0, 0, 9])
        self.assertEqual(result["trace"].shape[-1], 10)  # Empty pipeline for L=1.

    def test_overtaking_same_day_merging_and_due_date_pipeline(self):
        spec = Scenario("cross", lead_time_values=(1, 3), lead_time_probabilities=(0.5, 0.5))

        def policy(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
            return 10.0 if quoted_lead_time == 3 else 20.0

        result = simulate_callable(policy, _tape([5, 5, 5, 5], [3, 1, 1, 1]), spec, 4, 0, True)
        trace = result["trace"][0]
        np.testing.assert_array_equal(trace[:, 0], [0, 0, 20, 30])
        np.testing.assert_array_equal(trace[1, 10:], [0, 10])
        np.testing.assert_array_equal(trace[2, 10:], [10, 0])
        np.testing.assert_array_equal(trace[:, 8], [0, 0, 15, 40])
        self.assertEqual(result["total_cost"][0], 75)

    def test_last_demand_interface_and_current_demand_not_passed(self):
        observed = []

        def policy(**kwargs):
            self.assertEqual(set(kwargs), {"on_hand_inventory", "pipeline_orders", "last_demand", "quoted_lead_time"})
            observed.append((kwargs["last_demand"], kwargs["quoted_lead_time"]))
            return 0.0

        spec = Scenario("manual", lead_time_values=(1, 3), lead_time_probabilities=(0.5, 0.5))
        result = simulate_callable(policy, _tape([7, 12, 1], [3, 1, 3], initial=99), spec, 3, 0)
        self.assertEqual(observed, [(99, 3), (7, 1), (12, 3)])
        self.assertEqual(result["total_cost"][0], 40)  # Every quote consumed despite zero orders.

    def test_pipeline_mutation_cannot_modify_arrivals(self):
        def mutate(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
            pipeline_orders[:] = 99999
            return 10.0

        spec = scenario_specs()[4]
        tapes = generate_tapes(spec, 2, 171, 40)
        reference = simulate_callable(_constant_ten, tapes, spec, 25, 5, True)
        modified = simulate_callable(mutate, tapes, spec, 25, 5, True)
        np.testing.assert_array_equal(reference["trace"], modified["trace"])
        np.testing.assert_array_equal(reference["total_cost"], modified["total_cost"])

    def test_burnin_uses_real_demand_and_preserves_state(self):
        spec = Scenario("manual", lead_time_values=(1,))
        tapes = _tape([7, 12, 1], [1, 1, 1])
        result = simulate_callable(_constant_ten, tapes, spec, 1, 2, True)
        self.assertEqual(result["total_cost"][0], 9)
        self.assertEqual(result["demand_units"][0], 1)
        self.assertEqual(result["trace"][0, 2, 2], 12)
        np.testing.assert_array_equal(result["trace"][0, :, 9], [0, 0, 1])
        np.testing.assert_array_equal(result["order_matrix"], [[10]])
        np.testing.assert_array_equal(result["cost_matrix"], [[[9, 0]]])

    def test_nested_horizons_share_actual_trajectory(self):
        spec = scenario_specs()[5]
        tapes = generate_tapes(spec, 2, 771, 1000)
        full = simulate_callable(_numba_policy, tapes, spec, 500, 500, True)
        for horizon in (50, 100, 200):
            short = simulate_callable(_numba_policy, tapes, spec, horizon, 500, True)
            np.testing.assert_array_equal(short["trace"], full["trace"][:, :500 + horizon])
            costs = full["trace"][:, 500:500 + horizon, 8] + 2 * full["trace"][:, 500:500 + horizon, 7]
            np.testing.assert_allclose(short["total_cost"], costs.sum(axis=1), rtol=1e-14)

    def test_actions_and_short_tapes_fail_closed(self):
        spec = Scenario("manual", lead_time_values=(1,))
        tapes = _tape([1, 2], [1, 1])
        for invalid in (-1, float("nan"), float("inf"), True, "1", np.array([1])):
            with self.assertRaises(InvalidPolicyError):
                simulate_callable(lambda **kwargs: invalid, tapes, spec, 2, 0)
        for horizon, burnin in ((3, 0), (1, 2), (0, 0), (1, -1)):
            with self.assertRaises(ValueError):
                simulate_callable(_constant_ten, tapes, spec, horizon, burnin)

    def test_compiled_and_reference_share_all_transitions(self):
        from numba import njit
        compiled = njit(_numba_policy)
        for spec in scenario_specs():
            tapes = generate_tapes(spec, 3, 1009, 80)
            reference = simulate_callable(_numba_policy, tapes, spec, 50, 20, True)
            accelerated = simulate_compiled(compiled, tapes, spec, 50, 20, True)
            for field in ("total_cost", "holding_cost", "lost_sales_cost", "demand_units", "sales_units", "lost_units", "trace"):
                np.testing.assert_array_equal(reference[field], accelerated[field])


if __name__ == "__main__":
    unittest.main()
