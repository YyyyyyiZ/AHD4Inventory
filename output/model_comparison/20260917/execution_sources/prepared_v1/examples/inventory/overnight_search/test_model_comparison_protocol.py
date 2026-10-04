"""Synthetic protocol checks: no model calls, demand generation, or policy runs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from . import model_comparison as runner


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def policy(label):
    return (
        f"# Synthetic fixture: {label}\n"
        "def compute_order_amount(age, pipeline, mu, cv, f, L):\n"
        '    S = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":60.0}\n'
        "    return S\n"
    )


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="model-protocol-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.specs = runner.specifications()
        self.discovery = [s for s in self.specs if s["m"] in (3, 5, 7)]
        self.protocol = {
            "discovery_m": [3, 5, 7], "transfer_m": [4, 8],
            "repetitions": 3, "independent_initial_candidates": 4,
            "stages": {
                "train": {"paths": 16, "burnin": 200, "horizon": 512, "budget": 512},
                "promote": {"paths": 32, "burnin": 500, "horizon": 1000,
                            "budget": 1536, "top_k": 3},
                "validation": {"paths": 32, "burnin": 500, "horizon": 1000},
                "refit": {"paths": 32, "burnin": 500, "horizon": 1500, "budget": 1536},
                "test": {"paths": 128, "burnin": 500, "horizon": 3000},
            },
        }
        write_json(self.root / "protocol.json", self.protocol)
        # Fail closed if a future runner change bypasses the mocked job boundary.
        for name in ("evaluate_comparison", "make_client"):
            mocked = patch.object(runner, name, side_effect=AssertionError(
                "Synthetic tests must never execute policies or create API clients"))
            mocked.start()
            self.addCleanup(mocked.stop)

    def record(self, specs=None, cost=100.0, offset=0.0):
        return {
            "valid": True, "parameters": {"S": {"min": 0.0, "max": 60.0}},
            "results": {
                s["name"]: {"cost": cost, "theta": [s["m"] + offset],
                            "metrics": [0.1, 0.2, 0.3], "nfev": 1,
                            "seconds": 0.0, "transitions": 1}
                for s in (self.discovery if specs is None else specs)
            },
        }

    def row(self, origin, score):
        return {"origin": origin, "score": score, "code": policy(origin),
                "train": self.record()}

    def test_first_four_prompts_ignore_previous_candidates_and_failures(self):
        common = [self.row("common:seed", 1.0)]
        later = self.row("previous_candidate_marker", 0.1)
        failures = [{"origin": "previous_failure_marker", "error": "synthetic timeout"}]
        reference = runner.prompt_for(0, common, common, [])
        for index in range(4):
            with self.subTest(index=index):
                actual = runner.prompt_for(index, common + [later], common, failures)
                self.assertEqual(reference, actual)
                self.assertNotIn("previous_candidate_marker", actual)
                self.assertNotIn("previous_failure_marker", actual)
        evolved = runner.prompt_for(4, common + [later], common, failures)
        self.assertIn("previous_candidate_marker", evolved)
        self.assertIn("previous_failure_marker", evolved)

    def test_split_and_fresh_stage_repeat_seeds_are_common_across_backbones(self):
        expected = {(m, cv, f) for m in (3, 4, 5, 7, 8)
                    for cv in (1.5, 2.0) for f in (0.0, 0.5)}
        self.assertEqual(len(self.specs), 20)
        self.assertEqual({(s["m"], s["cv"], s["f"]) for s in self.specs}, expected)
        self.assertEqual(len(self.discovery), 12)
        self.assertEqual(len([s for s in self.specs if s["m"] in (4, 8)]), 8)
        seed_values = set()
        for repeat in (1, 2, 3):
            for phase in self.protocol["stages"]:
                specs = self.specs if phase in {"refit", "test"} else None
                jobs = [runner.make_job(self.root, policy(model), phase, repeat, specs=specs)
                        for model in ("reasoning", "cheap", "control")]
                reference = jobs[0]
                self.assertEqual(len(reference["scenarios"]), 20 if specs else 12)
                self.assertTrue(reference["cache_actions"])
                for job in jobs[1:]:
                    for field in ("seed", "scenario_seeds", "optimizer_seed", "scenarios",
                                  "paths", "burnin", "horizon", "op"):
                        self.assertEqual(reference[field], job[field], (phase, repeat, field))
                current = set(reference["scenario_seeds"].values())
                self.assertEqual(len(current), len(reference["scenarios"]))
                self.assertFalse(seed_values.intersection(current), (phase, repeat))
                seed_values.update(current)
                if phase not in {"refit", "test"}:
                    self.assertEqual({s["m"] for s in reference["scenarios"]}, {3, 5, 7})

    def test_transfer_warm_start_preserves_cv_fifo_and_ties_choose_lower_m(self):
        fitted = {"results": {s["name"]: {"theta": [float(s["m"]), s["cv"], s["f"]]}
                              for s in self.discovery}}
        warm = runner.warm_for_all_specs(fitted)
        self.assertEqual(set(warm), {s["name"] for s in self.specs})
        for s in self.specs:
            source_m = {4: 3, 8: 7}.get(s["m"], s["m"])
            self.assertEqual(warm[s["name"]], [[float(source_m), s["cv"], s["f"]]])

    def selection_fixture(self):
        rows = [self.row("generated:bad", 0.5), self.row("generated:second", 0.6),
                self.row("generated:third", 0.7), self.row("generated:not_promoted", 0.8),
                self.row("common:seed", 1.0)]
        folder = self.root / "runs" / "synthetic" / "r1"
        write_json(folder / "completed.json", {"pool": rows})
        write_json(self.root / "common" / "r1" / "denominators.json",
                   {s["name"]: 100.0 for s in self.discovery})
        return rows, folder

    def test_failed_promotion_retained_common_seed_can_win_without_replacements(self):
        rows, folder = self.selection_fixture()
        requested = []

        def fake_saved_job(path, job, **kwargs):
            phase = Path(path).stem
            requested.append((phase, job))
            if phase == "promote" and job["code"] == rows[0]["code"]:
                result = {"valid": False, "error_type": "timeout", "error": "synthetic"}
            else:
                is_seed = job["code"] == rows[-1]["code"]
                result = self.record(job["scenarios"], cost=90.0 if is_seed else 120.0, offset=10.0)
                result["request_sha256"] = runner.fingerprint(job)
            write_json(path, result)
            return result

        with patch.object(runner, "saved_job", side_effect=fake_saved_job):
            frozen = runner.select_and_freeze(self.root, "synthetic", 1)
        self.assertEqual(frozen["origin"], "common:seed")
        selected = runner.read(folder / "selected.json")
        self.assertEqual([(x["origin"], x["phase"]) for x in selected["failures"]],
                         [("generated:bad", "promote")])
        promoted_codes = [job["code"] for phase, job in requested if phase == "promote"]
        self.assertEqual(promoted_codes, [row["code"] for row in rows[:3]] + [rows[-1]["code"]])
        self.assertFalse(any(job["code"] == rows[3]["code"] for _, job in requested))
        self.assertFalse(any(phase == "validation" and job["code"] == rows[0]["code"]
                             for phase, job in requested))
        refit = [job for phase, job in requested if phase == "refit"]
        self.assertEqual(len(refit), 1)
        self.assertEqual(len(refit[0]["scenarios"]), 20)
        for s in self.specs:
            source_m = {4: 3, 8: 7}.get(s["m"], s["m"])
            self.assertEqual(refit[0]["warm_starts"][s["name"]], [[source_m + 10.0]])

    def test_all_selection_failures_leave_repeat_unfrozen(self):
        _, folder = self.selection_fixture()
        with patch.object(runner, "saved_job", return_value={"valid": False, "error_type": "timeout"}) as mocked:
            with self.assertRaisesRegex(ValueError, "All predeclared selection candidates failed"):
                runner.select_and_freeze(self.root, "synthetic", 1)
        self.assertEqual(mocked.call_count, 4)
        self.assertEqual(len(runner.read(folder / "selected.json")["failures"]), 4)
        self.assertFalse((folder / "freeze.json").exists())

    def test_final_test_gate_requires_every_model_and_all_three_repeats(self):
        models = [{"slug": name, "role": "control" if name == "control" else "candidate"}
                  for name in ("reasoning", "cheap", "control")]
        write_json(self.root / "models.json", {"models": models})
        missing = None
        for model in models:
            for repeat in (1, 2, 3):
                code = policy(model["slug"])
                frozen = {"slug": model["slug"], "repeat": repeat, "code": code,
                          "code_sha256": hashlib.sha256(code.encode()).hexdigest(),
                          "theta": {s["name"]: [1.0] for s in self.specs}}
                path = self.root / "runs" / model["slug"] / f"r{repeat}" / "freeze.json"
                if model["slug"] == "control" and repeat == 3:
                    missing = (path, frozen)
                else:
                    write_json(path, frozen)
        with patch.object(runner, "make_job") as make_job, patch.object(runner, "saved_job") as saved_job:
            with self.assertRaises(FileNotFoundError):
                runner.test_all(self.root)
            make_job.assert_not_called()
            saved_job.assert_not_called()
        self.assertFalse((self.root / "all_models_frozen.json").exists())
        write_json(*missing)
        with patch.object(runner, "saved_job", return_value={"valid": True}) as saved_job, patch("builtins.print"):
            runner.test_all(self.root)
        self.assertEqual(saved_job.call_count, 18)
        self.assertEqual(len(runner.read(self.root / "all_models_frozen.json")), 9)
        for call in saved_job.call_args_list:
            job = call.args[1]
            self.assertEqual(job["op"], "evaluate")
            self.assertEqual(len(job["scenarios"]), 20)


if __name__ == "__main__":
    unittest.main()
