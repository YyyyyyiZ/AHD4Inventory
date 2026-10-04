"""Generation-boundary and resume tests; API and numerical work are mocked."""
from contextlib import ExitStack
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from . import model_comparison as runner
from .model_comparison_client import ClientConfig, FrozenPricing, ModelComparisonClient


def code(index):
    return (f"# fixture_candidate={index}\n"
            "def compute_order_amount(age, pipeline, mu, cv, f, L):\n"
            '    S = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":200.0}\n'
            "    return S\n")


def training(index):
    return {"valid": True, "parameters": {"S": {}}, "results": {"s": {
        "cost": 100.0 - index - .1, "theta": [float(index)],
        "metrics": [0., 0., 0.], "nfev": 9, "seconds": .01, "transitions": 9}}}


class GenerationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="generation_mock_")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "run"
        self.root.mkdir()
        credential = Path(temporary.name) / "credentials.json"
        credential.write_text(json.dumps({"credentials": [{"api_key": "mock-generation-key",
            "allowed_origin": "https://mock.invalid"}]}))
        credential.chmod(0o600)
        self.config = {"generations": 2, "proposals_per_generation": 3,
                       "independent_initial_candidates": 3, "generated_candidates_per_repetition": 6,
                       "llm_max_output_tokens": 65536}
        self.calls, self.jobs = [], []
        self.invalid = set()
        self.crash_index = None
        self.fail_transport = False
        def transport(**kwargs):
            index = len(self.calls)
            self.calls.append(kwargs["payload"])
            if self.fail_transport:
                raise TimeoutError("mock failure")
            return {"model": "deepseek-flash", "id": f"mock-{index}",
                    "usage": {"cost": .001, "prompt_tokens": 20, "completion_tokens": 30},
                    "choices": [{"finish_reason": "stop", "message": {"content": code(index)}}]}
        config = ClientConfig("flash_r1", "https://mock.invalid/chat/completions", "deepseek-flash",
                              FrozenPricing(".3", ".006", "1.2"), endpoint_confirmed=True)
        self.client = ModelComparisonClient(config, self.root / "api_budget", 30., credential, transport=transport)
        self.folder = self.root / "runs/flash/r1"
        self.baseline = {"origin": "common:seed", "code": code(-1), "score": 1., "train": training(-1)}
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(runner, "prepare", side_effect=lambda _: self.config))
        stack.enter_context(patch.object(runner, "configured_models", return_value=[{"slug": "flash", "role": "candidate"}]))
        stack.enter_context(patch.object(runner, "make_baselines", return_value=({"seed": self.baseline}, {"s": 100.})))
        self.make_client = stack.enter_context(patch.object(runner, "make_client", return_value=self.client))
        def make_job(root, source, phase, repeat, **kwargs):
            return {"code": source, **kwargs}
        stack.enter_context(patch.object(runner, "make_job", side_effect=make_job))
        def saved_job(path, job):
            index = int(re.search(r"fixture_candidate=(-?\d+)", job["code"])[1])
            self.jobs.append((index, job))
            if index == self.crash_index:
                raise RuntimeError("mock numerical interruption")
            if index in self.invalid:
                return {"valid": False, "error_type": "timeout", "error": f"failure_candidate_{index}"}
            return training(index)
        stack.enter_context(patch.object(runner, "saved_job", side_effect=saved_job))
        stack.enter_context(patch("builtins.print"))

    def run_model(self):
        return runner.run_model(self.root, "flash", 1)

    def test_ten_by_ten_uses_only_frozen_prior_generations(self):
        self.config.update(generations=10, proposals_per_generation=10,
                           independent_initial_candidates=10, generated_candidates_per_repetition=100)
        completed = self.run_model()
        self.assertEqual(len(self.calls), 100)
        self.assertEqual(len(completed["pool"]), 101)
        self.assertEqual(completed["generation_protocol"]["generations"], 10)
        for index, payload in enumerate(self.calls):
            generation = index // 10
            prompt = payload["messages"][-1]["content"]
            self.assertEqual(payload["max_tokens"], 65536)
            self.assertIn(f"Generation {generation + 1}, proposal {index % 10 + 1} of 10.", prompt)
            observed_parents = [int(x) for x in re.findall(r"Candidate flash/r1/(\d+)", prompt)]
            self.assertTrue(all(parent < generation * 10 for parent in observed_parents))
            if generation == 0:
                self.assertEqual(observed_parents, [])
                self.assertIn("Independently propose a strong initial structure.", prompt)
            else:
                self.assertIn(generation * 10 - 1, observed_parents)
        for index, job in self.jobs:
            generation = index // 10
            if generation == 0:
                self.assertEqual(job["warm_starts"], {})
            else:
                self.assertEqual(job["warm_starts"]["s"], [[float(generation * 10 - 1)], [float(generation * 10 - 2)]])
        for generation in range(10):
            folder = self.folder / "generations" / f"{generation:02d}"
            snapshot, summary = runner.read(folder / "input.json"), runner.read(folder / "summary.json")
            self.assertEqual(len(snapshot["pool"]), 1 + 10 * generation)
            self.assertEqual(summary["status"], "complete")
            self.assertEqual((summary["valid"], summary["invalid"], summary["proposals_recorded"]), (10, 0, 10))
            self.assertEqual(summary["input_sha256"], runner.fingerprint(snapshot))
            self.assertEqual(summary["best_generated_so_far"]["origin"], f"flash/r1/{generation * 10 + 9:02d}")
            self.assertEqual(summary["best_after"]["source_kind"], "generated")
        for i in range(10):
            provenance = runner.read(self.folder / "candidates" / f"{i:02d}" / "generation_provenance.json")
            self.assertEqual(provenance["warm_start_parent_origins"], [])

    def test_failures_become_visible_only_in_next_generation(self):
        self.invalid = {0, 3}
        self.run_model()
        for index, payload in enumerate(self.calls):
            prompt = payload["messages"][-1]["content"]
            self.assertEqual("failure_candidate_0" in prompt, index >= 3)
            self.assertNotIn("failure_candidate_3", prompt)
        for generation in (0, 1):
            summary = runner.read(self.folder / "generations" / f"{generation:02d}" / "summary.json")
            self.assertEqual((summary["valid"], summary["invalid"]), (2, 1))

    def test_mid_generation_resume_reuses_response_and_snapshot(self):
        self.crash_index = 1
        with self.assertRaisesRegex(RuntimeError, "numerical interruption"):
            self.run_model()
        self.assertEqual(len(self.calls), 2)
        snapshot_path = self.folder / "generations/00/input.json"
        before = snapshot_path.read_bytes()
        self.crash_index = None
        completed = self.run_model()
        self.assertEqual(len(self.calls), 6)
        self.assertEqual(snapshot_path.read_bytes(), before)
        self.assertEqual(len(completed["pool"]), 7)
        self.assertEqual(runner.read(self.folder / "generations/01/summary.json")["status"], "complete")

    def test_changed_snapshot_is_rejected_before_further_api_attempts(self):
        self.crash_index = 1
        with self.assertRaises(RuntimeError):
            self.run_model()
        path = self.folder / "generations/00/input.json"
        value = runner.read(path)
        value["failures"].append({"origin": "tampered", "error": "not prior feedback"})
        runner.atomic_json(path, value)
        self.crash_index = None
        with self.assertRaisesRegex(ValueError, "Frozen record mismatch"):
            self.run_model()
        self.assertEqual(len(self.calls), 2)

    def test_unresolved_request_leaves_incomplete_generation_and_no_more_posts(self):
        self.fail_transport = True
        with self.assertRaisesRegex(RuntimeError, "no automatic retry"):
            self.run_model()
        with self.assertRaisesRegex(RuntimeError, "unresolved API opportunity"):
            self.run_model()
        self.assertEqual(len(self.calls), 1)
        summary = runner.read(self.folder / "generations/00/summary.json")
        self.assertEqual((summary["status"], summary["proposals_recorded"], summary["invalid"]),
                         ("incomplete_api_failure", 1, 1))
        self.assertFalse((self.folder / "completed.json").exists())

    def test_bad_generation_total_is_rejected_before_client_creation(self):
        self.config["generated_candidates_per_repetition"] = 7
        with self.assertRaisesRegex(ValueError, "candidate total"):
            self.run_model()
        self.make_client.assert_not_called()


class CatalogTests(unittest.TestCase):
    def test_standalone_flash_requires_single_candidate_and_no_control(self):
        with tempfile.TemporaryDirectory(prefix="flash_catalog_mock_") as temporary:
            root = Path(temporary)
            runner.atomic_json(root / "protocol.json", {"comparison_mode": "standalone_flash"})
            flash = {"slug": "flash", "role": "candidate", "client": {"model": "deepseek-flash"}}
            runner.atomic_json(root / "models.json", {"models": [flash]})
            self.assertEqual(runner.configured_models(root), [flash])
            runner.atomic_json(root / "models.json", {"models": [flash, {"slug": "control", "role": "control"}]})
            with self.assertRaisesRegex(ValueError, "exactly one"):
                runner.configured_models(root)

    def test_original_comparison_still_requires_control(self):
        with tempfile.TemporaryDirectory(prefix="legacy_catalog_mock_") as temporary:
            root = Path(temporary)
            runner.atomic_json(root / "protocol.json", {})
            runner.atomic_json(root / "models.json", {"models": [{"slug": "candidate", "role": "candidate"}]})
            with self.assertRaisesRegex(ValueError, "control"):
                runner.configured_models(root)


if __name__ == "__main__":
    unittest.main()
