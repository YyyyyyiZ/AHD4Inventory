"""Network-free integration of the PIL runtime with the original EOH optimizer."""
from __future__ import annotations

from contextlib import redirect_stdout
import gzip
import hashlib
import importlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from . import evolution, problem
from .adaptive_pil_runner import adaptive_runtime, jobs, source_hashes, verify_frozen
from .adaptive_pil_seed import seed_code
from .adaptive_pil_worker import prepare_policy
from .baselines import evaluate_baseline
from .data import generate_tapes, scenario_specs
from .test_adaptive_pil_worker import frozen_record, six_parameter_policy


class MockModelClient:
    """Final code replies only; no provider interface or credentials are used."""
    def __init__(self):
        self.calls = []

    def chat(self, messages, *, max_tokens, temperature, metadata):
        self.calls.append(dict(messages=messages, metadata=metadata,
                               max_tokens=max_tokens, temperature=temperature))
        code = six_parameter_policy(0.1 * (metadata["candidate_index"] + 1))
        return "```python\n" + code + "```\n{{Mock six-parameter helper-aware mutation.}}", {
            "cost": 0.0, "request_id": f"offline-{len(self.calls)}", "model": "offline-mock"}


def _save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def _bindings():
    return [(evolution, "TrainingProblem", evolution.TrainingProblem),
            (evolution, "prepare_policy", evolution.prepare_policy),
            (problem, "prepare_policy", problem.prepare_policy),
            (problem, "GetPrompts", problem.GetPrompts)]


class AdaptivePILRunnerTests(unittest.TestCase):
    def assert_bindings_restored(self, bindings):
        for module, name, original in bindings:
            self.assertIs(getattr(module, name), original, f"Binding was not restored: {name}")

    def test_real_m2_scipy_chain_accepts_six_params_and_preserves_best(self):
        scenario = scenario_specs()[-1]  # Regime dependence and random/overtaking leads.
        record = frozen_record(scenario)
        tapes = generate_tapes(scenario, 3, seed=735, n_periods=25)
        reference = evaluate_baseline(record, tapes, scenario, horizon=20, burnin=5, compiled=False)
        original_seed_cost = float(reference["total_cost"].mean())
        bindings = _bindings()
        framework = evolution._framework_modules()
        framework_bindings = [(framework["evolution"], "InterfaceLLM", framework["evolution"].InterfaceLLM),
                              (framework["interface"], "Evolution", framework["interface"].Evolution),
                              (framework["eoh"], "InterfaceEC", framework["eoh"].InterfaceEC),
                              (framework["analyzer"], "InventoryAnalyzer", framework["analyzer"].InventoryAnalyzer)]
        optimizer_module = importlib.import_module(framework["eoh"].__package__ + ".external_scipy")
        real_optimize = optimizer_module.ScipyOptimizer.optimize
        real_m2 = framework["evolution"].Evolution.m2
        optimizer_calls, m2_calls = [], []

        def observe_optimize(instance, *args, **kwargs):
            answer = real_optimize(instance, *args, **kwargs)
            optimizer_calls.append(dict(parameter_count=len(kwargs["opt_params"]),
                history_evaluations=len(answer.history or []), maxiter=instance.max_iter,
                uses_projection="conditional_projected_inventory(" in kwargs["original_code"],
                uses_arrival="conditional_arrival_mean(" in kwargs["original_code"]))
            return answer

        def observe_m2(instance, parent):
            m2_calls.append(hashlib.sha256(parent["code"].encode()).hexdigest())
            return real_m2(instance, parent)

        client = MockModelClient()
        with tempfile.TemporaryDirectory(prefix="adaptive-pil-integration-") as folder:
            output = Path(folder)
            with adaptive_runtime(record) as (adapter, source):
                self.assertEqual(len(prepare_policy(source)["opt_params"]), 5)
                self.assertIs(adapter, evolution)
                self.assertIsNot(evolution.TrainingProblem, bindings[0][2])
                _save(output / "initial_pool.json", [{"algorithm": "Frozen Adaptive PIL seed",
                                                       "code": source, "objective": None, "other_inf": None}])
                # Both wrappers delegate to the real implementation; no numerical
                # optimization or evolutionary operator is replaced by a mock.
                with patch.object(optimizer_module.ScipyOptimizer, "optimize", observe_optimize), \
                     patch.object(framework["evolution"].Evolution, "m2", observe_m2), \
                     redirect_stdout(io.StringIO()):
                    result = adapter.run_evolution(scenario=scenario, train_tapes=tapes,
                        output_dir=output, client=client, population_size=2, generations=1,
                        optimizer_maxiter=1, max_opt_params=None, burnin=5, horizon=20,
                        repeat=1, model_name="offline-mock", evaluation_timeout=60.)
                self.assertEqual(result["status"], "completed")
                self.assertFalse(result["test_evaluated"])
                self.assertEqual(result["model_calls"], 2)
                self.assertEqual(len(client.calls), 2)
                self.assertEqual(len(m2_calls), 2)
                self.assertEqual([call["parameter_count"] for call in optimizer_calls], [5, 6, 6])
                self.assertTrue(all(call["history_evaluations"] > 0 and call["maxiter"] == 1
                                    and call["uses_projection"] and call["uses_arrival"]
                                    for call in optimizer_calls))
                for call in client.calls:
                    self.assertEqual(call["metadata"]["operator"], "m2")
                    prompt = call["messages"][0]["content"]
                    self.assertIn("conditional_projected_inventory", prompt)
                    self.assertIn("conditional_arrival_mean", prompt)
                initial = json.loads((output / "pops/population_generation_0.json").read_text())[0]
                # The original framework stores objectives at five decimal
                # places. Check monotonicity within that documented rounding.
                self.assertLessEqual(initial["objective"], original_seed_cost + 1e-5)
                self.assertLessEqual(result["best_train_cost"], initial["objective"] + 1e-5)
                self.assertLessEqual(result["best_train_cost"], original_seed_cost + 1e-5)
                candidates = sorted((output / "candidates").glob("*.json.gz"))
                self.assertEqual(len(candidates), 2)
                for path in candidates:
                    with gzip.open(path, "rt") as handle:
                        saved = json.load(handle)
                    self.assertEqual(len(prepare_policy(saved["offspring"]["code"])["opt_params"]), 6)
                    self.assertTrue(np.isfinite(saved["offspring"]["objective"]))
                    self.assertEqual(saved["optimizer"]["name"], "L-BFGS-B")
                definition = json.loads((output / "search_definition.json").read_text())
                self.assertIsNone(definition["max_opt_params"])
                self.assertEqual(definition["operator"], "m2")
                self.assertEqual(definition["optimizer"], "SciPy L-BFGS-B")
                self.assertFalse(definition["test_access"])
                self.assertFalse((output / "evaluation").exists())
                # Saved candidate/seed replay must not request new mock responses.
                with redirect_stdout(io.StringIO()):
                    replay = adapter.run_evolution(scenario=scenario, train_tapes=tapes,
                        output_dir=output, client=client, population_size=2, generations=1,
                        optimizer_maxiter=1, max_opt_params=None, burnin=5, horizon=20,
                        repeat=1, model_name="offline-mock", evaluation_timeout=60.)
                self.assertEqual(len(client.calls), 2)
                self.assertEqual(replay["code_sha256"], result["code_sha256"])
                self.assertEqual(replay["best_train_cost"], result["best_train_cost"])
        self.assert_bindings_restored(bindings)
        self.assert_bindings_restored(framework_bindings)
        self.assertIs(optimizer_module.ScipyOptimizer.optimize, real_optimize)
        self.assertIs(framework["evolution"].Evolution.m2, real_m2)

    def test_runtime_bindings_restore_after_exception(self):
        bindings = _bindings()
        with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
            with adaptive_runtime(frozen_record(scenario_specs()[0])):
                raise RuntimeError("synthetic failure")
        self.assert_bindings_restored(bindings)

    def test_original_seed_is_retained_when_optimizer_reports_worse(self):
        framework = evolution._framework_modules()
        optimizer_module = importlib.import_module(framework["eoh"].__package__ + ".external_scipy")
        interface = framework["interface"].InterfaceEC.__new__(framework["interface"].InterfaceEC)
        interface.external_optimizer, interface.interface_eval = "scipy", None
        interface.max_iter, interface.timeout, interface.debug = 1, 5., False
        code = seed_code(frozen_record(scenario_specs()[0]))
        individual = dict(code=code, objective=100., opt_params=prepare_policy(code)["opt_params"])
        with patch.object(optimizer_module.ScipyOptimizer, "optimize",
                          return_value=SimpleNamespace(optimized_fitness=101., optimized_code="worse")):
            answer = interface.optimize_individual(individual)
        self.assertIs(answer, individual)
        self.assertEqual(answer["code"], code)
        self.assertEqual(answer["objective"], 100.)

    def test_seventeen_completions_cannot_pass_eighteen_policy_holdout_gate(self):
        with tempfile.TemporaryDirectory(prefix="adaptive-pil-gate-") as folder:
            root = Path(folder)
            _save(root / "source_manifest.json", {"sha256": source_hashes()})
            specs = {scenario.scenario_id: scenario for scenario in scenario_specs()}
            for sid, repeat in jobs()[:-1]:
                chain = root / "training" / sid / f"self_evolve_h200_r{repeat}"
                chain.mkdir(parents=True, exist_ok=True)
                code = seed_code(frozen_record(specs[sid]))
                (chain / "policy.py").write_text(code)
                _save(chain / "completed.json", dict(status="completed", full_protocol=True,
                    scenario_id=sid, repeat=repeat, source_training_horizon=200,
                    best_code_path=str(chain / "policy.py"), code_sha256=hashlib.sha256(code.encode()).hexdigest()))
                _save(chain / "warmstart_definition.json", {"fixture": True})
                _save(root / "baselines" / sid / "h200/records.json",
                      {"forecast_adaptive_pil": frozen_record(specs[sid])})
            with self.assertRaisesRegex(RuntimeError, "All 18"):
                verify_frozen(root, create=True)
            self.assertFalse((root / "all_policies_freeze.json").exists())


if __name__ == "__main__":
    unittest.main()
