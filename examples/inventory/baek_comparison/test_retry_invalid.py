"""Offline fabricated-record tests; never construct a real API transport."""
from dataclasses import asdict
import fcntl
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from .harness import SessionResult
from .retry_invalid import RetryNotEligible, plan_retry, retry_invalid
from .runner import atomic_json, recover_spend, sha256


class RetryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        self.session = "l1_poisson_r1"
        self.folder = self.run / "sessions" / self.session
        self.folder.mkdir(parents=True)
        self.prompt = "Frozen problem statement only.\n"
        self.code = "def compute_order_amount(on_hand_inventory, pipeline_orders):\n    return -1.0\n"
        self.spec = {"session_id": self.session, "level": "L1", "family": "poisson", "repeat": 1,
                     "scenario_id": "poisson_L6_c1_2", "prompt_sha256": sha256(self.prompt.encode())}
        self.manifest = {"sessions": [self.spec], "spend_limit_usd_including_preflight_and_retries": 30}
        atomic_json(self.run / "manifest.json", self.manifest)
        self.original = {**self.spec, **asdict(SessionResult(status="completed", final_code=self.code,
                                                           requests=1, cost_usd=0.2)),
                         "code_sha256": sha256(self.code.encode())}
        atomic_json(self.folder / "result.json", self.original)
        (self.folder / "prompt.txt").write_text(self.prompt)
        (self.folder / "policy.py").write_text(self.code)
        self.events = [{"event": "request", "max_request_cost_usd": 0.8},
                       {"event": "response", "response": {"id": "synthetic-response", "status": "completed",
                                                            "usage": {"cost": 0.2}}},
                       {"event": "session_end", "result": {"status": "completed"}}]
        (self.folder / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in self.events))
        atomic_json(self.run / "api_smoke_response.json", {"usage": {"cost": 0.001}})
        self.validation = self.run / "validation/poisson_L6_c1_2" / ("baek_" + self.session + ".json")
        self.write_validation()

    def write_validation(self, status="invalid", stage="policy_action", error_type="ValueError"):
        self.validation_record = {
            "evaluation_kind": "synthetic_contract_validation", "source": "baek_generated",
            "scenario_id": self.spec["scenario_id"], "data_sha256": {},
            "code_sha256": sha256(self.code.encode()),
            "manifest_sha256": sha256((self.run / "manifest.json").read_bytes()),
            "metadata": {"session_id": self.session, "attempt": 1,
                         "result_sha256": sha256((self.folder / "result.json").read_bytes())},
            "status": status, "raw_result": {"status": status,
                "error": {"type": error_type, "message": "synthetic contract failure", "stage": stage}},
            "evaluation_limits": {"setup_timeout_seconds": 600, "action_timeout_seconds": 1,
                                  "worker_timeout_seconds": 1200},
            "batches": {"synthetic_contract": {"summary": {"mean_total_cost": 999999999}}},
        }
        atomic_json(self.validation, self.validation_record)

    def test_plan_has_no_execution_or_file_mutation(self):
        before = {p: p.read_bytes() for p in self.folder.iterdir()}
        def forbidden():
            raise AssertionError("Default plan must not access credentials or create sandbox")
        plan = retry_invalid(self.run, self.session, sandbox_factory=forbidden, key_loader=forbidden)
        self.assertTrue(plan["eligible"])
        self.assertEqual(plan["attempt"], 2)
        self.assertAlmostEqual(plan["spent_usd_before_retry"], 0.201)
        self.assertEqual(before, {p: p.read_bytes() for p in self.folder.iterdir()})

    def test_approved_conservative_bounds_allow_eligibility_but_remain_in_budget(self):
        holds = [
            {"log": "first/events.jsonl", "request_index": 28, "reserved_usd": 0.952908,
             "blocks_resume": False, "reconciled_for_resume": True,
             "charge_resolution": "conservative_bound", "actual_cost_usd": None},
            {"log": "second/events.jsonl", "request_index": 20, "reserved_usd": 0.819808,
             "blocks_resume": False, "reconciled_for_resume": True,
             "charge_resolution": "conservative_bound", "actual_cost_usd": None},
        ]
        spent = 0.201 + sum(item["reserved_usd"] for item in holds)
        before = (self.folder / "result.json").read_bytes()
        with patch("examples.inventory.baek_comparison.retry_invalid.recover_spend",
                   return_value=(spent, holds)):
            plan = retry_invalid(self.run, self.session)
        self.assertTrue(plan["eligible"])
        self.assertAlmostEqual(plan["spent_usd_before_retry"], 1.973716)
        self.assertEqual(before, (self.folder / "result.json").read_bytes())
        self.assertFalse((self.folder / "retry_1").exists())
        for extra in (
            {"reserved_usd": 0.4, "blocks_resume": True},
            {"reserved_usd": 0.4},
        ):
            with self.subTest(extra=extra), patch(
                "examples.inventory.baek_comparison.retry_invalid.recover_spend",
                return_value=(spent + 0.4, holds + [extra]),
            ):
                with self.assertRaisesRegex(RetryNotEligible, "Unresolved paid requests"):
                    retry_invalid(self.run, self.session)

    def test_explicit_mock_retry_preserves_first_attempt_and_exact_prompt(self):
        first_bytes = (self.folder / "result.json").read_bytes()
        seen = []
        class Sandbox:
            def probe(self):
                pass
        class Harness:
            def __init__(inner, **kwargs):
                inner.kwargs = kwargs
            def run(inner, prompt):
                seen.append(prompt)
                budget = inner.kwargs["budget"]
                budget.reserve(0.5)
                budget.settle(0.5, 0.3)
                events = [{"event": "request", "max_request_cost_usd": 0.5},
                          {"event": "response", "response": {"usage": {"cost": 0.3}}}]
                inner.kwargs["log_path"].write_text("".join(json.dumps(e) + "\n" for e in events))
                return SessionResult(status="completed", final_code="def compute_order_amount(on_hand_inventory, pipeline_orders):\n    return 0.0\n", cost_usd=0.3, requests=1)
        record = retry_invalid(self.run, self.session, execute=True, harness_factory=Harness,
                               sandbox_factory=Sandbox, key_loader=lambda: "fake-offline-key")
        self.assertEqual(seen, [self.prompt])
        self.assertEqual(record["attempt"], 2)
        self.assertEqual(record["parent_session_id"], self.session)
        self.assertEqual((self.folder / "result.json").read_bytes(), first_bytes)
        self.assertEqual((self.folder / "policy.py").read_text(), self.code)
        self.assertAlmostEqual(recover_spend(self.run)[0], 0.501)
        self.assertEqual((self.folder / "retry_1/prompt.txt").read_bytes(), self.prompt.encode())
        with self.assertRaises(RetryNotEligible):
            plan_retry(self.run, self.session)

    def test_poor_valid_and_review_or_infrastructure_results_never_qualify(self):
        for status in ("ok", "review_required", "worker_failed", "hash_mismatch"):
            with self.subTest(status=status):
                self.write_validation(status=status)
                with self.assertRaises(RetryNotEligible):
                    plan_retry(self.run, self.session)
        self.write_validation(status="timeout", stage="stationarity_probe")
        with self.assertRaises(RetryNotEligible):
            plan_retry(self.run, self.session)

    def test_actual_policy_or_setup_timeout_qualifies(self):
        for stage in ("setup", "policy_action"):
            self.write_validation(status="timeout", stage=stage, error_type="EvaluationTimeout")
            self.assertTrue(plan_retry(self.run, self.session)["eligible"])
        self.validation_record["evaluation_limits"]["setup_timeout_seconds"] = 0.01
        atomic_json(self.validation, self.validation_record)
        with self.assertRaises(RetryNotEligible):
            plan_retry(self.run, self.session)

    def test_wrong_hash_or_test_based_evidence_never_qualifies(self):
        self.validation_record["code_sha256"] = "incorrect"
        atomic_json(self.validation, self.validation_record)
        with self.assertRaises(RetryNotEligible):
            plan_retry(self.run, self.session)
        self.write_validation()
        self.validation_record["evaluation_kind"] = "frozen_policy_scoring"
        atomic_json(self.validation, self.validation_record)
        with self.assertRaises(RetryNotEligible):
            plan_retry(self.run, self.session)

    def test_missing_final_output_requires_real_response_and_same_prompt(self):
        self.original["status"] = "invalid_final_output"
        self.original["final_code"] = None
        atomic_json(self.folder / "result.json", self.original)
        plan = plan_retry(self.run, self.session)
        self.assertEqual(plan["invalidity_evidence"][0]["kind"], "invalid_final_output")
        (self.folder / "prompt.txt").write_text("changed prompt")
        with self.assertRaises(RetryNotEligible):
            plan_retry(self.run, self.session)

    def test_infrastructure_generation_status_cannot_retry(self):
        for status in ("transport_rejected", "uncertain_paid_failure", "budget_exhausted", "unexpected_model"):
            self.original["status"] = status
            atomic_json(self.folder / "result.json", self.original)
            with self.assertRaises(RetryNotEligible):
                plan_retry(self.run, self.session)

    def test_recursive_cost_recovery_keeps_pending_retry(self):
        retry = self.folder / "retry_1"
        retry.mkdir()
        (retry / "events.jsonl").write_text(json.dumps({"event": "request", "max_request_cost_usd": 0.7}) + "\n{partial")
        spent, uncertain = recover_spend(self.run)
        self.assertAlmostEqual(spent, 0.901)
        self.assertEqual(len(uncertain), 1)

    def test_running_generation_lock_blocks_even_retry_plan(self):
        with (self.run / ".runner.lock").open("a") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError):
                retry_invalid(self.run, self.session)


if __name__ == "__main__":
    unittest.main()
