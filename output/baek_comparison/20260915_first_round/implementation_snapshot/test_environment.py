"""Small independent trace and contract checks; no policy search or API calls."""

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from .environment import (
    CORE_SCENARIO_IDS,
    InvalidPolicyError,
    Scenario,
    adapt_order,
    discover_scenarios,
    load_demands,
    sample_demands,
    simulate_policy,
)


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.scenario = Scenario("trace", "poisson", 2, horizon=3)

    def test_l2_arrivals_and_hand_calculated_costs(self):
        observed = []

        def policy(*, on_hand_inventory, pipeline_orders):
            observed.append((on_hand_inventory, tuple(pipeline_orders)))
            return 3.0

        result = simulate_policy(policy, self.scenario, [[4, 1, 5]])
        # Two planning orders arrive at selling periods 0 and 1. End stocks
        # during selling are 0, 2, 0; losses are 1, 0, 0. h=1, p=2.
        self.assertEqual(observed, [(0, (0,)), (0, (3,)), (3, (3,)), (3, (3,)), (5, (3,))])
        np.testing.assert_array_equal(result.total_cost, [4])
        np.testing.assert_array_equal(result.holding_cost, [2])
        np.testing.assert_array_equal(result.lost_sales_cost, [2])
        np.testing.assert_array_equal(result.demand_units, [10])
        np.testing.assert_array_equal(result.sales_units, [9])
        np.testing.assert_array_equal(result.lost_units, [1])
        np.testing.assert_array_equal(result.service_level, [0.9])
        self.assertEqual(result.periods_scored, 3)
        self.assertEqual(result.periods_simulated, 5)

    def test_pipeline_mutation_cannot_change_environment(self):
        def policy(*, on_hand_inventory, pipeline_orders):
            pipeline_orders.clear()
            pipeline_orders.append(10_000)
            return 3

        result = simulate_policy(policy, self.scenario, [[4, 1, 5]])
        np.testing.assert_array_equal(result.total_cost, [4])

    def test_policy_gets_no_current_or_future_demand(self):
        records = []

        def policy(**kwargs):
            self.assertEqual(set(kwargs), {"on_hand_inventory", "pipeline_orders"})
            records.append((kwargs["on_hand_inventory"], tuple(kwargs["pipeline_orders"])))
            return 3

        simulate_policy(policy, self.scenario, [[4, 1, 5]])
        first = records[:]
        records.clear()
        simulate_policy(policy, self.scenario, [[400, 100, 500]])
        # Before the first selling demand has occurred, both paths are identical.
        self.assertEqual(first[:3], records[:3])

    def test_invalid_actions_fail_instead_of_being_silently_repaired(self):
        for action in (-1, float("nan"), float("inf"), -float("inf"), "3", True, 1j, np.array([3]), 10**1000):
            with self.subTest(action=repr(action)), self.assertRaises(InvalidPolicyError):
                simulate_policy(adapt_order(lambda _i, _p: action), self.scenario, [[1, 1, 1]])

    def test_policy_exception_preserves_cause(self):
        def broken(_i, _p):
            raise RuntimeError("intentional")

        with self.assertRaises(InvalidPolicyError) as error:
            simulate_policy(adapt_order(broken), self.scenario, [[1, 1, 1]])
        self.assertIsInstance(error.exception.__cause__, RuntimeError)

    def test_uncapped_fractional_and_explicit_integer_orders(self):
        scenario = replace(self.scenario, horizon=2)
        half = adapt_order(lambda _i, _p: np.float64(0.5))
        result = simulate_policy(half, scenario, [[1, 1]])
        rounded = simulate_policy(half, scenario, [[1, 1]], integer_orders=True)
        np.testing.assert_array_equal(result.total_cost, [2])
        # np.rint ties-to-even sends each half-unit action to zero.
        np.testing.assert_array_equal(rounded.total_cost, [4])
        uncapped = simulate_policy(adapt_order(lambda _i, _p: 1_000_000), replace(scenario, horizon=1), [[0]])
        np.testing.assert_array_equal(uncapped.total_cost, [1_000_000])
        np.testing.assert_array_equal(uncapped.service_level, [1])

    def test_long_run_uses_stochastic_burn_in_without_zero_planning(self):
        result = simulate_policy(
            adapt_order(lambda _i, _p: 3), self.scenario,
            [[4, 1, 5, 1, 1]], mode="long_run", burn_in=2,
        )
        # Unscored stocks are 0,0. Scored end stocks are 0,2,4;
        # losses are 2,0,0. Only scored demand 5+1+1 contributes to service.
        np.testing.assert_array_equal(result.total_cost, [10])
        np.testing.assert_array_equal(result.holding_cost, [6])
        np.testing.assert_array_equal(result.lost_sales_cost, [4])
        np.testing.assert_array_equal(result.demand_units, [7])
        np.testing.assert_array_equal(result.sales_units, [5])
        self.assertEqual(result.periods_scored, 3)
        self.assertEqual(result.periods_simulated, 5)

    def test_lead_time_one_has_empty_policy_pipeline(self):
        def policy(*, on_hand_inventory, pipeline_orders):
            self.assertEqual(pipeline_orders, [])
            return 2

        result = simulate_policy(policy, replace(self.scenario, lead_time=1), [[2, 2, 2]])
        np.testing.assert_array_equal(result.total_cost, [0])

    def test_multiple_paths_reset_inventory_and_return_per_path_costs(self):
        result = simulate_policy(adapt_order(lambda _i, _p: 3), self.scenario, [[4, 1, 5], [0, 0, 0]])
        np.testing.assert_array_equal(result.total_cost, [4, 18])
        self.assertEqual(result.summary()["mean_total_cost"], 11)
        self.assertFalse(result.total_cost.flags.writeable)

    def test_wrong_horizon_or_invalid_demand_rejected(self):
        for demands in ([[1, 2]], [[1, -1, 2]], [[1, float("nan"), 2]], [[1, 1j, 2]], []):
            with self.subTest(demands=demands), self.assertRaises(ValueError):
                simulate_policy(adapt_order(lambda _i, _p: 0), self.scenario, demands)
        with self.assertRaises(ValueError):
            simulate_policy(adapt_order(lambda _i, _p: 0), self.scenario, [[1, 2, 3]], burn_in=1)
        with self.assertRaises(ValueError):
            simulate_policy(adapt_order(lambda _i, _p: 0), self.scenario, [[1, 2, 3]], mode="long_run", burn_in=3)

    def test_exact_distribution_transformations(self):
        class FixedDraws:
            def normal(self, mean, std, *, size):
                return np.array([[-1.5, -0.5, 0, 0.5, 1.5, 2.5]])

            def exponential(self, mean, *, size):
                return np.array([[0, 0.5, 1.5, 2.5, 3.5, 4.5]])

        with patch("numpy.random.default_rng", return_value=FixedDraws()):
            normal = sample_demands(Scenario("normal", "normal", 2, std_normal=30), 1, seed=0, horizon=6)
            exponential = sample_demands(Scenario("exp", "exponential", 2), 1, seed=0, horizon=6)
        np.testing.assert_array_equal(normal, [[0, 0, 0, 0, 2, 2]])
        np.testing.assert_array_equal(exponential, [[0, 0, 2, 2, 4, 4]])

    def test_seeded_sampling_is_repeatable_and_does_not_touch_global_rng(self):
        np.random.seed(123)
        expected = np.random.random(4)
        np.random.seed(123)
        for scenario_id in CORE_SCENARIO_IDS:
            scenario = Scenario.from_id(scenario_id)
            first = sample_demands(scenario, 2, seed=1234)
            second = sample_demands(scenario, 2, seed=1234)
            np.testing.assert_array_equal(first, second)
            self.assertEqual(first.shape, (2, 50))
            self.assertTrue(np.issubdtype(first.dtype, np.integer))
            self.assertTrue((first >= 0).all())
        np.testing.assert_array_equal(np.random.random(4), expected)

    def test_discovery_and_loading_validate_data_without_mutation(self):
        scenario = Scenario.from_id("poisson_L2_c1_2")
        self.assertEqual(scenario.mean_demand, 100)
        self.assertEqual(scenario.to_params()["lead_time"], 2)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            instance = {
                "initial_inventory": 0, "lead_time": 2, "holding_cost": 1,
                "lost_sales_cost": 2, "distribution": "poisson", "std_normal": None,
                "num_periods": 50, "demand": [2] * 50,
            }
            for split in ("train", "test"):
                (directory / f"{scenario.scenario_id}_{split}.json").write_text(json.dumps([instance]))
            self.assertEqual(discover_scenarios(directory), (scenario,))
            path = directory / f"{scenario.scenario_id}_train.json"
            before = path.read_bytes()
            demands = load_demands(scenario, "train", n_paths=1, data_dir=directory)
            self.assertEqual(demands.shape, (1, 50))
            self.assertEqual(path.read_bytes(), before)
            with self.assertRaises(ValueError):
                load_demands(scenario, "train", n_paths=2, data_dir=directory)
            (directory / f"{scenario.scenario_id}_test.json").unlink()
            with self.assertRaises(ValueError):
                discover_scenarios(directory)

    def test_existing_dataset_discovery_has_expected_30_scenarios(self):
        scenarios = discover_scenarios()
        self.assertEqual(len(scenarios), 30)
        ids = {scenario.scenario_id for scenario in scenarios}
        self.assertTrue(set(CORE_SCENARIO_IDS) <= ids)
        self.assertEqual({scenario.lead_time for scenario in scenarios}, {2, 4, 6})
        self.assertEqual({scenario.lost_sales_cost for scenario in scenarios}, {2, 5})

    def test_parity_with_existing_simulator_on_six_training_paths(self):
        from examples.inventory.evaluation.best5.utils.inventory_sim import simulate_instance_order_before_sell_fn

        # This stored, inspected policy is a simple max(0,100-I-sum(pipeline))
        # mapping. Re-use its source to check the exact existing callable path.
        inventory_directory = Path(__file__).resolve().parent.parent
        namespace = {}
        source = json.loads((inventory_directory / "base_stock.json").read_text())[0]["code"]
        exec(source, namespace)
        policy = namespace["compute_order_amount"]
        for scenario_id in CORE_SCENARIO_IDS:
            scenario = Scenario.from_id(scenario_id)
            demands = load_demands(scenario, "train", n_paths=2)
            result = simulate_policy(policy, scenario, demands)
            expected = []
            for demand in demands:
                instance = {
                    "lead_time": scenario.lead_time,
                    "holding_cost": scenario.holding_cost,
                    "lost_sales_cost": scenario.lost_sales_cost,
                    "initial_inventory": 0,
                    "num_periods": scenario.horizon,
                    "demand": demand.tolist(),
                }
                expected.append(simulate_instance_order_before_sell_fn(policy, instance))
            np.testing.assert_array_equal(result.total_cost, expected)


if __name__ == "__main__":
    unittest.main()
