"""Offline coverage for policies with no limit on tunable-parameter count."""
import importlib
import inspect
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from numba import njit

from .data import Scenario, generate_tapes
from .evolution import _framework_modules, _parse_response, run_evolution
from .fast_policy import FastPolicyWorker, prepare_policy
from .problem import TrainingProblem
from .prompts import GetPrompts


def parameter_policy(count):
    lines = ["def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):"]
    for index in range(count):
        value = 0.25 + index * 0.05
        config = {"initial": value, "min": 0.0, "max": 10.0, "type": "float"}
        lines.append(f"    coefficient_{index} = {value!r}  # OPT_PARAM: {config!r}")
    total = " + ".join(f"coefficient_{index}" for index in range(count))
    return "\n".join(lines + [f"    order_amount = max(0.0, {total})", "    return order_amount", ""])


class ParameterLimitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.framework = _framework_modules()
        cls.legacy_evolution = cls.framework["evolution"].Evolution
        cls.optimizer_module = importlib.import_module(
            cls.framework["eoh"].__package__ + ".external_scipy")

    def legacy_prompt(self, location, limit):
        # Prompt construction alone must never initialize a model client.
        obj = self.legacy_evolution.__new__(self.legacy_evolution)
        obj.param_loc, obj.param_num = location, limit
        return obj.external_optimizer_prompt()

    def test_defaults_and_prompts_have_no_parameter_count_limit(self):
        for target in (prepare_policy, FastPolicyWorker, TrainingProblem, run_evolution, _parse_response):
            self.assertIsNone(inspect.signature(target).parameters["max_opt_params"].default)
        self.assertIsNone(inspect.signature(self.legacy_evolution).parameters["param_num"].default)
        for location in ("default", "start"):
            prompt = self.legacy_prompt(location, None)
            self.assertIn("OPT_PARAM", prompt)
            self.assertNotIn("None", prompt)
            self.assertNotRegex(prompt.lower(), r"at most|more than|maximum of|eligible to be marked")
        prompt = GetPrompts(Scenario("offline")).get_other_inf()
        self.assertIn("OPT_PARAM", prompt)
        self.assertNotRegex(prompt.lower(), r"maximum of|parameters is allowed|at most|more than")

    def test_explicit_legacy_limits_still_apply(self):
        self.assertIn("at most 4 parameters", self.legacy_prompt("default", 4))
        self.assertIn("DON'T mark more than 10", self.legacy_prompt("start", 4))
        self.assertEqual(len(prepare_policy(parameter_policy(4), 4)["values"]), 4)
        self.assertEqual(len(prepare_policy(parameter_policy(12), 12)["values"]), 12)
        for count, limit in ((5, 4), (11, 10)):
            with self.subTest(count=count, limit=limit):
                with self.assertRaisesRegex(ValueError, "Too many OPT_PARAM"):
                    prepare_policy(parameter_policy(count), limit)

    def test_more_than_four_and_ten_parse_compile_and_preserve_every_value(self):
        for count in (5, 12):
            with self.subTest(count=count):
                code = parameter_policy(count)
                parsed, _, configs = _parse_response(f"```python\n{code}```\n{{{{Offline rule.}}}}")
                prepared = prepare_policy(parsed)
                self.assertEqual(len(configs), count)
                original, transformed = {}, {}
                exec(code, original)
                exec(prepared["source"], transformed)
                compiled = njit(transformed["compute_order_amount"], cache=False)
                state = (7.0, np.array([2.0, 4.0]), 3.0, 3)
                theta = np.asarray(prepared["values"])
                self.assertAlmostEqual(compiled(*state, theta), original["compute_order_amount"](*state))
                # Check every theta coordinate, including those beyond the old caps.
                initial = compiled(*state, theta)
                for index in range(count):
                    changed = theta.copy()
                    changed[index] += 0.125
                    self.assertAlmostEqual(compiled(*state, changed) - initial, 0.125)

    def test_twelve_parameters_reach_real_scipy_in_mock_evolution(self):
        code = parameter_policy(12)

        class OfflineClient:
            def __init__(self):
                self.prompts = []

            def chat(self, messages, **kwargs):
                self.prompts.append(messages[0]["content"])
                return f"```python\n{code}```\n{{{{Offline constant-order rule.}}}}", {"cost": 0.0}

        client = OfflineClient()
        dimensions = []
        real_minimize = self.optimizer_module.minimize

        def observe_minimize(fun, x0, *args, **kwargs):
            dimensions.append((len(x0), len(kwargs["bounds"]), kwargs["method"]))
            return real_minimize(fun, x0, *args, **kwargs)

        scenario = Scenario("offline_unlimited", lead_time_values=(1,), mean_demand=5.0)
        tapes = generate_tapes(scenario, 2, seed=7821, n_periods=12)
        with tempfile.TemporaryDirectory(prefix="unlimited-evolution-test-") as temporary:
            output = Path(temporary)
            with patch.object(self.optimizer_module, "minimize", side_effect=observe_minimize):
                result = run_evolution(scenario=scenario, train_tapes=tapes, output_dir=output,
                                       client=client, population_size=1, generations=1,
                                       optimizer_maxiter=1, burnin=2, horizon=10)
            self.assertEqual(result["status"], "completed")
            self.assertIn((12, 12, "L-BFGS-B"), dimensions)
            identity = json.loads((output / "search_definition.json").read_text())
            self.assertIsNone(identity["max_opt_params"])
            self.assertEqual(len(client.prompts), 1)
            self.assertNotRegex(client.prompts[0].lower(),
                                r"maximum of four|at most (?:4|10|none) parameters|more than 10 optimizable")
            evaluations = [json.loads(line) for line in
                           (output / "training_evaluations.jsonl").read_text().splitlines()]
            twelve = [row for row in evaluations if len(row["parameter_values"]) == 12]
            self.assertTrue(any(row["compiled_new"] for row in twelve))
            self.assertTrue(any(row["compact_optimizer_feedback"] for row in twelve))
            self.assertGreater(len({tuple(row["parameter_values"]) for row in twelve}), 12)


if __name__ == "__main__":
    unittest.main()
