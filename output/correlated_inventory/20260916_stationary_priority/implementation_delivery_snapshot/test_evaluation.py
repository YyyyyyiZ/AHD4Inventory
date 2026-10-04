"""Offline regressions for evaluation of short-lived compiled policies."""
import gc
import unittest
from unittest.mock import patch
import weakref

import numpy as np
from numba import njit
from numba.core.caching import FunctionCache, NullCache

from . import environment
from .data import Scenario, generate_tapes
from .evaluation import _use_process_local_kernel, from_trace


def dynamic_policy(target):
    def policy(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
        position = on_hand_inventory + 0.25 * np.sum(pipeline_orders)
        return max(0.0, target - position + 0.03 * last_demand + 0.1 * quoted_lead_time)
    return njit(policy, cache=False)


class EvaluationCacheTests(unittest.TestCase):
    def setUp(self):
        self.previous_kernel = environment._compiled_kernel
        environment._compiled_kernel = None

    def tearDown(self):
        environment._compiled_kernel = self.previous_kernel

    def test_new_and_existing_dispatcher_use_null_cache(self):
        new = _use_process_local_kernel()
        self.assertIsInstance(new._cache, NullCache)
        existing = njit(environment.simulate_kernel, cache=True)
        environment._compiled_kernel = existing
        self.assertIs(_use_process_local_kernel(), existing)
        self.assertIsInstance(existing._cache, NullCache)

    def test_collected_dynamic_policies_match_scalar_without_disk_cache(self):
        kernel = _use_process_local_kernel()
        references = []
        scenarios = [Scenario("fixed"), Scenario("random", "regime",
            lead_time_values=(3, 9), lead_time_probabilities=(0.5, 0.5))]
        arrays = ("total_cost", "holding_cost", "lost_sales_cost", "demand_units",
                  "sales_units", "lost_units", "trace", "order_matrix", "cost_matrix")
        # A disk-cache attempt would reproduce the unsafe code path.  Dynamic
        # closures must remain safe after earlier callable objects are collected.
        with patch.object(FunctionCache, "load_overload", side_effect=AssertionError("disk cache read")), \
             patch.object(FunctionCache, "save_overload", side_effect=AssertionError("disk cache write")):
            for scenario in scenarios:
                tapes = generate_tapes(scenario, 3, seed=902, n_periods=40)
                for target in (70.0, 95.0, 120.0):
                    with self.subTest(scenario=scenario.scenario_id, target=target):
                        policy = dynamic_policy(target)
                        references.append(weakref.ref(policy))
                        compiled = environment.simulate_compiled(policy, tapes, scenario,
                            horizon=30, burnin=10, return_trace=True)
                        scalar = environment.simulate_callable(policy.py_func, tapes, scenario,
                            horizon=30, burnin=10, return_trace=True)
                        for name in arrays:
                            np.testing.assert_allclose(compiled[name], scalar[name], rtol=1e-12, atol=1e-10)
                        for a, b in zip(from_trace(compiled["trace"], scenario, [(0, 20), (10, 30)]),
                                        from_trace(scalar["trace"], scenario, [(0, 20), (10, 30)])):
                            for name in a:
                                np.testing.assert_allclose(a[name], b[name], rtol=1e-12, atol=1e-10)
                        del policy
                        gc.collect()
        self.assertIs(environment._compiled_kernel, kernel)
        self.assertEqual(len(kernel.signatures), 6)
        self.assertTrue(any(reference() is None for reference in references),
                        "Exercise actual dispatcher collection, not just new policy creation")


if __name__ == "__main__":
    unittest.main()
