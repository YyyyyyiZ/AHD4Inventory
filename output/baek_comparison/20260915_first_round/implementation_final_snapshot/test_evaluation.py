"""Tiny frozen-source checks; policy code runs only in the actual OS sandbox."""
import shutil
import sys
import unittest

from .environment import Scenario
from .evaluation import evaluate_artifact, evaluate_artifact_batches, numeric_design_params, review_source
from .sandbox import PythonSandbox


class SourceReviewTests(unittest.TestCase):
    def test_io_and_introspection_require_review_without_running(self):
        class NeverRun:
            def run(self, *args, **kwargs):
                raise AssertionError("Flagged code must not execute")

        for source in ("import os", "x=open('data')", "x=globals()", "reader=open", "import io", "x=thing.open('data')", "import sys", "x=f.__globals__"):
            result = evaluate_artifact(source, "L1", Scenario("trace", "poisson", 2, horizon=3), [[1, 1, 1]], NeverRun())
            self.assertEqual(result["status"], "review_required")

    def test_setup_timing_is_allowed(self):
        self.assertEqual(review_source("import time\nstart=time.perf_counter()\n")["status"], "passed")

    def test_numeric_parameters_exclude_identifiers_and_non_normal_std(self):
        scenario = Scenario.from_id("poisson_L6_c1_2")
        params = numeric_design_params(scenario)
        self.assertNotIn("scenario_id", params)
        self.assertNotIn("distribution", params)
        self.assertNotIn("std_normal", params)
        self.assertTrue(all(isinstance(value, (int, float)) for value in params.values()))
        self.assertEqual(numeric_design_params(Scenario.from_id("normal_std30_L6_c1_2"))["std_normal"], 30)


@unittest.skipUnless(shutil.which("sandbox-exec"), "macOS OS sandbox required")
class IsolatedEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sandbox = PythonSandbox(sys.executable)

    def setUp(self):
        self.scenario = Scenario("trace", "poisson", 2, horizon=3)

    def evaluate(self, source, level="L1", **kwargs):
        return evaluate_artifact(source, level, self.scenario, [[4, 1, 5]], self.sandbox, timeout_seconds=15, **kwargs)

    def test_l1_hand_trace_and_separate_policy_namespace(self):
        source = """
def compute_order_amount(on_hand_inventory, pipeline_orders):
    try:
        payload
    except NameError:
        return 3
    raise AssertionError('worker demand namespace leaked')
"""
        result = self.evaluate(source)
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result["per_path"]["total_cost"], [4])
        self.assertEqual(result["per_path"]["holding_cost"], [2])
        self.assertEqual(result["per_path"]["lost_sales_cost"], [2])
        self.assertGreaterEqual(result["setup_seconds"], 0)
        self.assertGreaterEqual(result["mean_action_seconds"], 0)

    def test_l2_build_once_for_multiple_batches_and_numeric_params(self):
        source = """
builds = 0
def design(params):
    global builds
    builds += 1
    assert builds == 1
    assert all(isinstance(value, (int, float)) for value in params.values())
    assert 'scenario_id' not in params and 'distribution' not in params
    def compute_order_amount(on_hand_inventory, pipeline_orders):
        return 3
    return compute_order_amount
"""
        result = evaluate_artifact_batches(source, "L2", self.scenario, [
            {"name": "finite", "demands": [[4, 1, 5]]},
            {"name": "long", "demands": [[4, 1, 5, 1, 1]], "mode": "long_run", "burn_in": 2},
        ], self.sandbox, timeout_seconds=15)
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result["batches"]["finite"]["per_path"]["total_cost"], [4])
        self.assertEqual(result["batches"]["long"]["per_path"]["total_cost"], [10])

    def test_counter_based_policy_is_invalid(self):
        source = """
counter=0
def compute_order_amount(on_hand_inventory, pipeline_orders):
    global counter
    counter += 1
    return counter
"""
        result = self.evaluate(source)
        self.assertEqual(result["status"], "invalid", result)
        self.assertIn("Nonstationary", result["error"]["message"])

    def test_hidden_mutation_requires_review_even_if_action_constant(self):
        source = """
counter=0
def compute_order_amount(on_hand_inventory, pipeline_orders):
    global counter
    counter += 1
    return 3
"""
        result = self.evaluate(source)
        self.assertEqual(result["status"], "review_required", result)
        self.assertTrue(result["stationarity_check"]["mutable_state_changed"])

    def test_action_clock_is_flagged_but_setup_clock_works(self):
        result = self.evaluate("import time\nstarted=time.perf_counter()\ndef compute_order_amount(on_hand_inventory,pipeline_orders):\n return 3\n")
        self.assertEqual(result["status"], "ok", result)
        result = self.evaluate("import time\ndef compute_order_amount(on_hand_inventory,pipeline_orders):\n return time.perf_counter()\n")
        self.assertEqual(result["status"], "review_required", result)

    def test_invalid_action_and_hang_are_failures(self):
        result = self.evaluate("def compute_order_amount(on_hand_inventory,pipeline_orders):\n return float('nan')\n")
        self.assertEqual(result["status"], "invalid", result)
        result = self.evaluate("def compute_order_amount(on_hand_inventory,pipeline_orders):\n while True: pass\n", action_timeout_seconds=0.05)
        self.assertEqual(result["status"], "timeout", result)

    def test_initialization_guard(self):
        result = self.evaluate("while True: pass\n", setup_timeout_seconds=0.05)
        self.assertEqual(result["status"], "timeout", result)
        self.assertIsNotNone(result["setup_seconds"])

    def test_l2_callable_object_requires_review_without_action_execution(self):
        for action in ("return 3", "raise AssertionError('callable object action must not execute')"):
            with self.subTest(action=action):
                source = (
                    "class ConstantPolicy:\n"
                    " def __call__(self, on_hand_inventory, pipeline_orders):\n"
                    "  " + action + "\n"
                    "def design(params):\n"
                    " return ConstantPolicy()\n"
                )
                result = self.evaluate(source, level="L2")
                self.assertEqual(result["status"], "review_required", result)
                self.assertEqual(result["error"]["type"], "CallableReviewRequired")
                self.assertEqual(result["batches"], {})
                self.assertNotIn("stationarity_check", result)

    def test_l2_noncallable_output_is_invalid(self):
        result = self.evaluate("def design(params):\n return 3\n", level="L2")
        self.assertEqual(result["status"], "invalid", result)
        self.assertEqual(result["error"]["type"], "TypeError")


if __name__ == "__main__":
    unittest.main()
