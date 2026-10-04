"""Offline action/trajectory equivalence of the editable Adaptive PIL seed."""
import ast
import json
import math
import unittest

import numpy as np
from numba import njit

from . import baselines
from .adaptive_pil_seed import (HELPER_NAMES, build_runtime_payload,
    make_helper_namespace, make_seed_policy, seed_code, seed_helpers_description,
    trusted_runtime_source)
from .data import Scenario, generate_tapes, scenario_specs
from .environment import simulate_kernel


def fixture_record(scenario):
    return {
        "name": "forecast_adaptive_pil", "version": baselines.VERSION,
        "scenario": scenario.to_dict(), "theta": [0.73, 0.92, 0.6, -0.15, 0.85],
        "forecast": {"inner_paths": 32, "seed": 9137, "grid_step": 0.25,
                     "latent_grid_limits": [-12.0, 12.0], "same_day_other_arrivals_included": True},
        "random_lead_interpretation": "committed-only projection",
    }


class AdaptivePILSeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kernel = staticmethod(njit(simulate_kernel, cache=False))
        cls.records = [fixture_record(s) for s in scenario_specs()]

    def test_actions_and_short_trajectories_match_original_all_scenarios(self):
        rng = np.random.default_rng(924)
        for record in self.records:
            scenario = Scenario(**record["scenario"])
            with self.subTest(scenario=scenario.scenario_id):
                original, seed = baselines.make_policy(record), make_seed_policy(record)
                last_demands = [0.0, 1e-6, 100 * math.log(2) - 1e-10,
                                100 * math.log(2), 100 * math.log(2) + 1e-10, 100.0, 1000.0, 8000.0]
                for last_demand in last_demands:
                    for quote in scenario.lead_time_values:
                        inventory = float(rng.uniform(0, 800))
                        pipeline = rng.uniform(0, 200, scenario.max_lead_time - 1)
                        before = pipeline.copy()
                        self.assertEqual(seed(inventory, pipeline, last_demand, quote),
                                         original(inventory, pipeline, last_demand, quote))
                        np.testing.assert_array_equal(pipeline, before)
                tapes = generate_tapes(scenario, 3, seed=471, n_periods=60)
                args = (tapes["demands"], tapes["lead_times"], tapes["initial_last_demand"],
                        scenario.max_lead_time, scenario.holding_cost, scenario.lost_sales_cost,
                        40, 20, True)
                left, right = self.kernel(original, *args), self.kernel(seed, *args)
                for a, b in zip(left, right):
                    np.testing.assert_array_equal(a, b)

    def test_payload_round_trip_is_read_only_and_has_no_policy_coefficients(self):
        record = self.records[-1]
        config, arrays = build_runtime_payload(record)
        self.assertNotIn("theta", config)
        self.assertTrue(all(not value.flags.writeable for value in arrays.values()))
        source = trusted_runtime_source()
        self.assertFalse(any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(ast.parse(source))))
        namespace = {"np": np, "math": math, "njit": njit}
        exec(source, namespace)
        helpers = namespace["make_helper_namespace"](json.loads(json.dumps(config)), arrays)
        self.assertEqual(set(helpers), set(HELPER_NAMES))
        observed = helpers["conditional_arrival_mean"](110.0, 3)
        arrays["means"].setflags(write=True)
        arrays["means"][:] = 0.0
        self.assertEqual(helpers["conditional_arrival_mean"](110.0, 3), observed)

    def test_one_period_analytic_case_and_same_day_other_arrivals(self):
        one = Scenario("one", lead_time_values=(1,))
        helpers = make_helper_namespace(fixture_record(one))
        inventory = 83.0
        expected = inventory + one.mean_demand * math.expm1(-inventory / one.mean_demand)
        self.assertEqual(helpers["conditional_projected_inventory"](inventory, np.empty(0), 93.0, 1), expected)
        record = self.records[-1]
        projected = make_helper_namespace(record)["conditional_projected_inventory"]
        pipeline = np.zeros(8)
        pipeline[2] = 17.0
        self.assertEqual(projected(0.0, pipeline, 100.0, 3), 17.0)

    def test_helpers_reject_unsafe_indices_and_nonphysical_inputs(self):
        helpers = make_helper_namespace(self.records[-1])
        mean = helpers["conditional_arrival_mean"]
        projected = helpers["conditional_projected_inventory"]
        pipeline = np.zeros(8)
        for quote in (0, 10, 3.5, float("nan")):
            with self.subTest(quote=quote):
                with self.assertRaises(ValueError):
                    mean(100.0, quote)
                with self.assertRaises(ValueError):
                    projected(0.0, pipeline, 100.0, quote)
        for inventory, arrivals, last in ((-1.0, pipeline, 100.0),
                                          (0.0, np.zeros(2), 100.0),
                                          (0.0, np.full(8, -1.0), 100.0),
                                          (0.0, np.full(8, np.inf), 100.0),
                                          (0.0, pipeline, float("nan"))):
            with self.assertRaises(ValueError):
                projected(inventory, arrivals, last, 3)

    def test_visible_source_preserves_coefficients_and_expanded_iid_bounds(self):
        record = fixture_record(scenario_specs()[0])
        record["theta"] = [0.7, 5.0, 0.0, 0.0, 0.3]
        record["search"] = {
            "full_parameter_bounds": [[0, 3], [0, 3], [-1, 3], [-1, 3], [0, 2]],
            "active_parameter_indices": [0, 1, 4],
            "rounds": [{"bounds": [[0, 3], [0, 6], [0, 2]]}],
        }
        code = seed_code(record)
        configs = [json.loads(line.split("OPT_PARAM:")[1]) for line in code.splitlines() if "OPT_PARAM:" in line]
        self.assertEqual([c["initial"] for c in configs], record["theta"])
        self.assertEqual(configs[1]["max"], 6.0)
        self.assertIn("target - inventory_gain * projected_inventory", code)
        self.assertIn("conditional_arrival_mean(last_demand, quoted_lead_time)", code)
        description = seed_helpers_description(record).lower()
        self.assertNotRegex(description, r"maximum of|at most|more than .*parameters")
        self.assertIn("committed-only", description)


if __name__ == "__main__":
    unittest.main()
