"""Offline tests of the isolated adaptive-PIL seed evaluation boundary."""
from dataclasses import asdict
import unittest

import numpy as np

from .adaptive_pil_worker import AdaptivePILWorker, prepare_policy
from .baselines import VERSION as BASELINE_VERSION, evaluate_baseline
from .data import generate_tapes, scenario_specs


SIGNATURE = "def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):\n"


def frozen_record(scenario):
    return {"name": "forecast_adaptive_pil", "version": BASELINE_VERSION, "scenario": asdict(scenario),
            "theta": [1.1, 1.6, 0.5, 0.3, 0.85],
            "forecast": {"inner_paths": 32, "seed": 81173, "grid_step": 0.05,
                         "same_day_other_arrivals_included": True}}


def six_parameter_policy(extra=0.0):
    source = SIGNATURE
    for name, value in zip(("target_scale", "cap_scale", "target_gain", "cap_gain", "inventory_gain", "extra_gain"),
                           (1.1, 1.6, 0.5, 0.3, 0.85, extra)):
        source += f"    {name} = {value!r}  # OPT_PARAM: {{'initial': {value!r}, 'min': 0.0, 'max': 5.0, 'type': 'float'}}\n"
    return source + (
        "    forecast = conditional_arrival_mean(last_demand, quoted_lead_time)\n"
        "    projected = conditional_projected_inventory(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time)\n"
        "    target = max(0.0, 100.0 * target_scale + target_gain * (forecast - 100.0))\n"
        "    cap = max(0.0, 100.0 * cap_scale + cap_gain * (forecast - 100.0))\n"
        "    return min(cap, max(0.0, target - inventory_gain * projected + extra_gain * last_demand))\n")


class AdaptivePILWorkerTests(unittest.TestCase):
    def test_unlimited_parameters_and_numeric_structure_cache_key(self):
        first, second = (prepare_policy(six_parameter_policy(value)) for value in (0.0, 0.2))
        self.assertEqual(len(first["opt_params"]), 6)
        self.assertEqual(first["structure_sha256"], second["structure_sha256"])
        self.assertNotEqual(first["code_sha256"], second["code_sha256"])
        with self.assertRaisesRegex(ValueError, "Too many"):
            prepare_policy(six_parameter_policy(), max_opt_params=4)

    def test_existing_isolation_restrictions_and_helper_names(self):
        forbidden = (
            "import os\n"+SIGNATURE+"    return 0.0\n",
            SIGNATURE+"    return open('/etc/passwd')\n",
            SIGNATURE+"    return conditional_arrival_mean.__globals__\n",
            SIGNATURE+"    pipeline_orders[0] = 1.0\n    return 0.0\n",
            SIGNATURE+"    conditional_arrival_mean = 1.0\n    return 0.0\n",
            "import math as conditional_arrival_mean\n"+SIGNATURE+"    return 0.0\n",
            "import numpy as np\n"+SIGNATURE+"    return np.load('forecast_bank.npz')\n",
        )
        for code in forbidden:
            with self.subTest(code=code), self.assertRaises(ValueError):
                prepare_policy(code)

    def test_seed_worker_matches_frozen_baseline_all_six_scenarios(self):
        from .adaptive_pil_seed import seed_code
        for scenario in scenario_specs():
            with self.subTest(scenario=scenario.scenario_id):
                record = frozen_record(scenario)
                tapes = generate_tapes(scenario, 2, seed=40013, n_periods=25)
                reference = evaluate_baseline(record, tapes, scenario, horizon=20, burnin=5,
                                              return_trace=True, compiled=False)
                code = seed_code(record)
                self.assertEqual(len(prepare_policy(code)["opt_params"]), 5)
                with AdaptivePILWorker(tapes, scenario, baseline_record=record, burnin=5, horizon=20) as worker:
                    result = worker.evaluate(code)
                    np.testing.assert_allclose(result["trajectory"], reference["total_cost"], rtol=1e-12, atol=1e-9)
                    np.testing.assert_allclose(result["order_matrix"], reference["order_matrix"], rtol=1e-12, atol=1e-9)
                    np.testing.assert_allclose(result["cost_matrix"], reference["cost_matrix"], rtol=1e-12, atol=1e-9)
                    compact = worker.evaluate(code, compact=True)
                    self.assertFalse(compact["compiled_new"])
                    self.assertEqual(compact["order_matrix"], [])
                    self.assertEqual(compact["trajectory"], result["trajectory"])

    def test_helpers_with_six_parameters_and_window_protocol(self):
        scenario = scenario_specs()[-1]
        record = frozen_record(scenario)
        tapes = generate_tapes(scenario, 3, seed=774, n_periods=40)
        reference = evaluate_baseline(record, tapes, scenario, horizon=30, burnin=10,
                                      return_trace=True, compiled=False)
        code = six_parameter_policy()
        with AdaptivePILWorker(tapes, scenario, baseline_record=record, burnin=10, horizon=30) as worker:
            result = worker.evaluate(code)
            self.assertEqual(len(result["opt_params"]), 6)
            np.testing.assert_allclose(result["trajectory"], reference["total_cost"], rtol=1e-12, atol=1e-9)
            changed = worker.evaluate(six_parameter_policy(0.2))
            self.assertFalse(changed["compiled_new"])
            self.assertEqual(changed["compilation_count"], 1)
            self.assertFalse(np.array_equal(changed["trajectory"], result["trajectory"]))
            window = worker.evaluate_windows(code, [(10,30), (0,20)])["windows"]
            np.testing.assert_allclose(window[0]["total_cost"], reference["total_cost"], rtol=1e-12, atol=1e-9)
            np.testing.assert_allclose(window[0]["order_units"], reference["order_matrix"].sum(axis=1), rtol=1e-12, atol=1e-9)
            cold = evaluate_baseline(record, tapes, scenario, horizon=20, burnin=0, compiled=False)
            np.testing.assert_allclose(window[1]["total_cost"], cold["total_cost"], rtol=1e-12, atol=1e-9)
            with self.assertRaises(ValueError):
                worker.evaluate(SIGNATURE+"    return demand_paths[0,0,0]\n")
        self.assertTrue(worker._proc.stdin.closed)
        self.assertTrue(worker._proc.stdout.closed)

    def test_record_scenario_mismatch_fails_before_child_launch(self):
        scenario, other = scenario_specs()[:2]
        tapes = generate_tapes(scenario, 1, seed=8, n_periods=2)
        with self.assertRaisesRegex(ValueError, "differs"):
            AdaptivePILWorker(tapes, scenario, baseline_record=frozen_record(other), burnin=0, horizon=2)


if __name__ == "__main__":
    unittest.main()
