"""Paid-opportunity resume checks; all API and numerical work is mocked."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error

from . import model_comparison as runner
from .model_comparison_client import ClientConfig, FrozenPricing, ModelComparisonClient


CODE = "def compute_order_amount(age, pipeline, mu, cv, f, L):\n    return 1.0\n"


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="comparison_resume_mock_")
        self.root = Path(self.temporary.name) / "run"
        self.root.mkdir()
        self.credential = Path(self.temporary.name) / "credentials.json"
        self.key = "mock-resume-key-not-real"
        self.credential.write_text(json.dumps({"credentials": [{"api_key": self.key,
            "allowed_origin": "https://mock.invalid"}]}))
        self.credential.chmod(0o600)
        self.config = ClientConfig("mock_r1", "https://mock.invalid/v1/chat/completions", "mock-model",
            FrozenPricing("1", ".1", "1"), endpoint_confirmed=True)
        self.calls = 0
        self.transport_failure = False
        self.response_override = None
        self.http_failure = None

        def transport(**kwargs):
            self.calls += 1
            if self.transport_failure:
                raise TimeoutError("Must not persist " + self.key + " or PRIVATE_REASONING")
            if self.http_failure is not None:
                failure = urllib.error.HTTPError("https://mock.invalid", self.http_failure, "Mock authentication failure", {}, None)
                failure.close()
                raise failure
            response = {"id": "mock-generation", "model": "mock-model",
                    "usage": {"cost": .001, "prompt_tokens": 10, "completion_tokens": 20},
                    "choices": [{"finish_reason": "stop", "message": {"content": CODE}}]}
            return self.response_override(response) if self.response_override else response
        self.client = ModelComparisonClient(self.config, self.root / "api_budget", 1., self.credential,
                                            transport=transport)
        self.folder = self.root / "runs/mock/r1"
        self.candidate = self.folder / "candidates/00"
        self.train = {"valid": True, "parameters": {}, "results": {"s": {
            "cost": 1., "theta": [], "metrics": [0, 0, 0], "nfev": 0}}}
        baseline = {"origin": "common:a", "code": CODE, "score": 1., "train": self.train}
        self.stack = ExitStack()
        self.prepare = self.stack.enter_context(patch.object(runner, "prepare", return_value={"generated_candidates_per_repetition": 1}))
        self.stack.enter_context(patch.object(runner, "configured_models", return_value=[{"slug": "mock", "role": "control"}]))
        self.stack.enter_context(patch.object(runner, "make_baselines", return_value=({"a": baseline}, {"s": 1.})))
        self.stack.enter_context(patch.object(runner, "make_client", return_value=self.client))
        self.stack.enter_context(patch.object(runner, "prompt_for", return_value="Write one policy."))
        self.stack.enter_context(patch.object(runner, "make_job", return_value={"mock_job": True}))
        self.saved_job = self.stack.enter_context(patch.object(runner, "saved_job", return_value=self.train))
        self.stack.enter_context(patch("builtins.print"))

    def tearDown(self):
        self.stack.close()
        self.temporary.cleanup()

    def run_model(self):
        return runner.run_model(self.root, "mock", 1)

    def reserve_legacy(self):
        return self.client.ledger.reserve("mock_r1", ".05", request_metadata={
            "metadata": {"slug": "mock", "repeat": 1, "candidate": 0}})

    def test_unknown_charge_failure_is_checkpointed_and_never_resent(self):
        self.prepare.return_value["generated_candidates_per_repetition"] = 16
        self.transport_failure = True
        with self.assertRaisesRegex(RuntimeError, "no automatic retry"):
            self.run_model()
        self.assertEqual(self.calls, 1)
        self.assertTrue((self.candidate / "api_attempt.json").exists())
        self.assertFalse((self.candidate / "response.json").exists())
        failure = runner.read(self.candidate / "api_failure.json")
        self.assertEqual(len(failure["ledger_attempts"]), 1)
        self.assertEqual(failure["ledger_attempts"][0]["state"], "unknown_charge")
        self.assertGreater(self.client.summary()["held_upper_usd"], 0)
        with self.assertRaisesRegex(RuntimeError, "unresolved API opportunity"):
            self.run_model()
        self.assertEqual(self.calls, 1)
        self.assertFalse((self.folder / "completed.json").exists())
        self.assertEqual(runner.read(self.folder / "api_incomplete.json")["status"], "incomplete_api_failure")
        self.saved_job.assert_not_called()
        for path in self.root.rglob("*.json"):
            text = path.read_text()
            self.assertNotIn(self.key, text)
            self.assertNotIn("PRIVATE_REASONING", text)

    def test_legacy_pending_ledger_without_runner_marker_prevents_post(self):
        request_id = self.reserve_legacy()
        with self.assertRaisesRegex(RuntimeError, "unresolved API opportunity"):
            self.run_model()
        self.assertEqual(self.calls, 0)
        row = runner.read(self.candidate / "record.json")
        self.assertFalse(row["valid"])
        self.assertEqual(row["api_failure"]["ledger_attempts"][0]["request_id"], request_id)
        self.assertEqual(self.client.summary()["held_upper_usd"], .05)

    def test_marker_before_reservation_is_conservatively_consumed(self):
        runner.atomic_json(self.candidate / "api_attempt.json", {"interrupted_before_receipt": True})
        with self.assertRaisesRegex(RuntimeError, "unresolved API opportunity"):
            self.run_model()
        self.assertEqual(self.calls, 0)
        self.assertEqual(self.client.summary()["requests"], 0)
        self.assertFalse(runner.read(self.candidate / "record.json")["valid"])

    def test_successful_client_receipt_recovers_after_runner_write_crash(self):
        original_write = runner.atomic_json
        def crash(path, value):
            if Path(path) == self.candidate / "response.json":
                raise OSError("simulated runner response write failure")
            return original_write(path, value)
        with patch.object(runner, "atomic_json", side_effect=crash):
            with self.assertRaises(OSError):
                self.run_model()
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.client.summary()["actual_cost_usd"], .001)
        self.assertFalse((self.candidate / "record.json").exists())
        self.run_model()
        self.assertEqual(self.calls, 1)
        self.assertTrue(runner.read(self.candidate / "record.json")["valid"])
        self.assertIn("recovered_from", runner.read(self.candidate / "response.json"))
        self.saved_job.assert_called_once()

    def test_saved_success_receipt_with_pending_money_remains_incomplete(self):
        request_id = self.reserve_legacy()
        runner.atomic_json(self.client.ledger.directory / "requests" / request_id / "response.json", {
            "request_id": request_id, "model_matches": True, "bounds_exceeded": False,
            "response_error": None, "cost_status": "actual", "finish_reason": "stop", "content": CODE,
            "actual_cost_usd": .001})
        with self.assertRaisesRegex(RuntimeError, "unresolved API opportunity"):
            self.run_model()
        self.assertEqual(self.calls, 0)
        self.assertFalse(runner.read(self.candidate / "record.json")["valid"])
        self.assertEqual(self.client.summary()["held_upper_usd"], .05)
        self.assertFalse((self.folder / "completed.json").exists())

    def test_http_401_stops_without_consuming_remaining_opportunities(self):
        self.prepare.return_value["generated_candidates_per_repetition"] = 16
        self.http_failure = 401
        with self.assertRaisesRegex(RuntimeError, "no automatic retry"):
            self.run_model()
        with self.assertRaisesRegex(RuntimeError, "unresolved API opportunity"):
            self.run_model()
        self.assertEqual(self.calls, 1)
        self.assertEqual(runner.read(self.candidate / "api_failure.json")["ledger_attempts"][0]["http_status"], 401)
        self.assertFalse((self.folder / "completed.json").exists())

    def test_unrecognized_model_stops_and_preserves_actual_charge(self):
        self.prepare.return_value["generated_candidates_per_repetition"] = 16
        def wrong_model(response):
            response["model"] = "unexpected-model"
            return response
        self.response_override = wrong_model
        with self.assertRaisesRegex(RuntimeError, "no automatic retry"):
            self.run_model()
        with self.assertRaisesRegex(RuntimeError, "unresolved API opportunity"):
            self.run_model()
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.client.summary()["actual_cost_usd"], .001)
        self.assertIsNotNone(self.client.summary()["paused_reason"])
        self.assertFalse((self.folder / "completed.json").exists())

    def test_missing_token_usage_stops_even_with_reported_actual_cost(self):
        self.prepare.return_value["generated_candidates_per_repetition"] = 16
        def cost_only(response):
            response["usage"] = {"cost": .001}
            return response
        self.response_override = cost_only
        with self.assertRaisesRegex(RuntimeError, "unresolved API opportunity"):
            self.run_model()
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.client.summary()["actual_cost_usd"], .001)
        self.assertFalse((self.folder / "completed.json").exists())
        self.saved_job.assert_not_called()

    def test_settled_code_parse_failure_is_candidate_failure_and_can_continue(self):
        self.prepare.return_value["generated_candidates_per_repetition"] = 2
        def first_invalid(response):
            if self.calls == 1:
                response["choices"][0]["message"]["content"] = "No policy code here."
            return response
        self.response_override = first_invalid
        completed = self.run_model()
        self.assertEqual(self.calls, 2)
        self.assertEqual(len(completed["failures"]), 1)
        self.assertFalse(runner.read(self.candidate / "record.json")["valid"])
        self.assertFalse(runner.read(self.candidate / "api_failure.json")["blocks_repetition"])
        self.assertFalse((self.folder / "api_incomplete.json").exists())
        self.assertEqual(self.client.summary()["actual_cost_usd"], .002)
        self.saved_job.assert_called_once()

    def test_paused_shared_ledger_stops_before_post(self):
        self.prepare.return_value["generated_candidates_per_repetition"] = 16
        with self.client.ledger.locked() as ledger:
            ledger["paused_reason"] = "Mock accounting review"
        with self.assertRaisesRegex(RuntimeError, "no automatic retry"):
            self.run_model()
        with self.assertRaisesRegex(RuntimeError, "unresolved API opportunity"):
            self.run_model()
        self.assertEqual(self.calls, 0)
        self.assertFalse((self.folder / "completed.json").exists())

    def test_two_concurrent_resumers_send_once(self):
        barrier = threading.Barrier(2)
        def prompt(*args):
            barrier.wait(5)
            return "Write one policy."
        with patch.object(runner, "prompt_for", side_effect=prompt):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: self.run_model(), range(2)))
        self.assertEqual(len(results), 2)
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.client.summary()["requests"], 1)


if __name__ == "__main__":
    unittest.main()
