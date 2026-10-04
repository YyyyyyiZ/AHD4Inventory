"""Offline forecast, information, and compiled/scalar baseline checks."""
from dataclasses import asdict
import unittest
import numpy as np

from .data import Scenario, generate_tapes
from .baselines import (PARAMETERS, forecast_bank, make_policy, evaluate,
                        _residual_from_paths, _signal_bracket, fit_baselines)


def record(name, scenario, theta, n=64):
    return {"name": name, "scenario": asdict(scenario), "theta": theta,
            "forecast": {"inner_paths": n, "seed": 81173, "grid_step": 0.05}}


class BaselineTests(unittest.TestCase):
    def test_pil_one_period_hand_calculation(self):
        # With I=2 and D equally 1 or 3, E[(I-D)+]=0.5, not [I-E D]+=0.
        paths = np.array([[[1.0], [3.0]]])
        residual = _residual_from_paths(2.0, np.empty(0), 1, 0, 0, 0.0, paths, np.zeros((2, 1)), 0.0)
        self.assertEqual(residual, 0.5)
        scenario = Scenario("l1", lead_time_values=(1,), lead_time_probabilities=(1.0,))
        policy = make_policy(record("conditional_pil", scenario, [1.0]))
        expected_residual = 100.0 + 100.0 * np.expm1(-1.0)
        self.assertAlmostEqual(policy(100.0, np.empty(0), 12.0, 1), 100.0 - expected_residual, places=11)

    def test_multi_period_lost_sales_and_arrival_timing(self):
        # Sample 1: (1-4)+=0, then (0+5-2)+=3; sample 2: (1-0)+=1, (1+5-9)+=0.
        paths = np.array([[[4.0, 2.0], [0.0, 9.0]]])
        residual = _residual_from_paths(1.0, np.array([5.0]), 2, 0, 0, 0.0, paths, np.zeros((2, 2)), 0.0)
        self.assertEqual(residual, 1.5)
        # A subsequent order arriving next period adds exactly its quantity.
        continuation = np.array([[0.0, 1.0], [0.0, 1.0]])
        with_orders = _residual_from_paths(1.0, np.array([5.0]), 2, 0, 0, 0.0, paths, continuation, 10.0)
        self.assertEqual(with_orders, 10.0)

    def test_pil_includes_other_orders_due_on_current_orders_arrival_day(self):
        paths = np.zeros((1, 2, 4))
        pipeline = np.array([0.0, 0.0, 7.0, 0.0])
        counts = np.array([[0., 0., 0., 1.], [0., 0., 0., 2.]])
        no_continuation = _residual_from_paths(0.0, pipeline, 3, 0, 0, 0.0, paths, counts, 0.0)
        self.assertEqual(no_continuation, 7.0)
        with_continuation = _residual_from_paths(0.0, pipeline, 3, 0, 0, 0.0, paths, counts, 10.0)
        self.assertEqual(with_continuation, 22.0)
        # The analytic L=1 exponential branch must include the same-day old order too.
        spec = Scenario("random_one", lead_time_values=(1, 3), lead_time_probabilities=(.5, .5))
        policy = make_policy(record("conditional_pil", spec, [1.0]))
        self.assertAlmostEqual(policy(0.0, np.array([7.0, 0.0]), 100.0, 1), 93.0)

    def test_conditional_forecast_directions(self):
        for rho in (0.8, -0.6):
            spec = Scenario("ar", "ar1", rho_latent=rho)
            code, signals, paths, means, continuation = forecast_bank(spec, 64)
            def forecast(last):
                lo, hi, w = _signal_bracket(last, code, signals)
                return means[lo] + w * (means[hi] - means[lo])
            low, high = forecast(20.0), forecast(200.0)
            self.assertEqual(high[0] > low[0], rho > 0)
            self.assertGreater(high[1], low[1])
        regime = Scenario("regime", "regime")
        _, _, _, means, _ = forecast_bank(regime, 64)
        self.assertGreater(means[1, 0], means[0, 0])
        self.assertAlmostEqual((means[0, 0] + means[1, 0]) / 2, 100.0)

    def test_iid_fixed_forecast_cbs_degeneracy(self):
        spec = Scenario("iid")
        regular = make_policy(record("capped_base_stock", spec, [6.0, 0.9]))
        forecast = make_policy(record("forecast_capped_base_stock", spec, [6.0, 0.9, 1.7, -0.8]))
        for previous in (0.0, 50.0, 500.0):
            pipeline = np.array([70.0, 30.0, 0.0, 20.0, 100.0])
            self.assertEqual(regular(90.0, pipeline, previous, 6), forecast(90.0, pipeline, previous, 6))
        _, _, paths0, means0, _ = forecast_bank(spec, 64)
        _, _, paths1, means1, _ = forecast_bank(Scenario("arzero", "ar1", rho_latent=0), 64)
        np.testing.assert_array_equal(paths0, paths1)
        np.testing.assert_array_equal(means0, means1)

    def test_frozen_policy_stationarity_and_no_future_demand(self):
        spec = Scenario("regime", "regime")
        saved = record("forecast_adaptive_pil", spec, [1.0, 1.5, 0.5, 0.5, 1.0])
        policy = make_policy(saved)
        pipeline = np.array([70.0, 30.0, 0.0, 20.0, 100.0])
        first = policy(10.0, pipeline, 80.0, 6)
        policy(500.0, np.zeros(5), 1.0, 6)
        self.assertEqual(first, policy(10.0, pipeline, 80.0, 6))
        tapes = generate_tapes(spec, 2, seed=123, n_periods=15)
        alternate = {k: v.copy() if isinstance(v, np.ndarray) else {} for k, v in tapes.items()}
        alternate["demands"][:, 7:] = 10000.0
        a = evaluate(saved, tapes, horizon=15, burnin=0, return_trace=True)
        b = evaluate(saved, alternate, horizon=15, burnin=0, return_trace=True)
        np.testing.assert_array_equal(a["trace"][:, :8, 4], b["trace"][:, :8, 4])

    def test_compiled_scalar_parity(self):
        spec = Scenario("random", "regime", lead_time_values=(3, 9), lead_time_probabilities=(0.5, 0.5))
        tapes = generate_tapes(spec, 3, seed=102, n_periods=30)
        examples = {
            "constant_order": [0.8], "base_stock": [6.0], "capped_base_stock": [6.0, 1.0],
            "forecast_capped_base_stock": [6.0, 1.0, 0.8, 0.2], "conditional_pil": [1.1],
            "forecast_adaptive_pil": [1.1, 1.5, 0.5, 0.5, 0.8], "pil_cop_continuation": [1.1, 0.8],
        }
        for name, theta in examples.items():
            with self.subTest(name=name):
                saved = record(name, spec, theta)
                a = evaluate(saved, tapes, horizon=20, burnin=10, compiled=True, return_trace=True)
                b = evaluate(saved, tapes, horizon=20, burnin=10, compiled=False, return_trace=True)
                np.testing.assert_allclose(a["trace"], b["trace"], rtol=1e-12, atol=1e-10)
                np.testing.assert_allclose(a["total_cost"], b["total_cost"], rtol=1e-12)

    def test_future_lead_continuation_overtaking(self):
        fixed = forecast_bank(Scenario("fixed"), 64)
        self.assertTrue((fixed[-1][:, :6] == 0).all())
        random = forecast_bank(Scenario("random", lead_time_values=(3, 9), lead_time_probabilities=(0.5, 0.5)), 64)
        self.assertGreater(random[-1][:, 4:9].sum(), 0)
        self.assertTrue((random[-1][:, :4] == 0).all())


if __name__ == "__main__":
    unittest.main()
