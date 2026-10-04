"""Offline checks for cancellation while preserved tools finish."""
from contextlib import ExitStack, redirect_stdout
from dataclasses import asdict
import hashlib
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from . import runner
from .harness import OpenRouterHarness, RunBudget, SessionConfig, SessionResult


class RecoveryCircuitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.run_dir = Path(self.temporary.name)
        self.credentials = self.run_dir / "fake_credentials.json"
        self.credentials.write_text(json.dumps({"api_key": "offline-test-placeholder"}))
        self.specs = [
            {"session_id": name, "level": "L1"}
            for name in ("waiting", "broken", "queued")
        ]
        for spec in self.specs:
            folder = self.run_dir / "sessions" / spec["session_id"]
            folder.mkdir(parents=True)
            (folder / "prompt.txt").write_text("offline fixture")
            (folder / "events.jsonl").write_text("")
        self.harness = Mock(side_effect=AssertionError("No inference may start after recovery failure"))
        self.stack = self.enterContext(ExitStack())
        self.stack.enter_context(patch.object(runner, "DEFAULT_CREDENTIALS", self.credentials))
        self.stack.enter_context(patch.object(runner, "prepare", return_value={"sessions": self.specs}))
        self.stack.enter_context(patch.object(runner, "recover_spend", return_value=(0.0, [])))
        self.stack.enter_context(patch.object(runner, "PythonSandbox"))
        self.stack.enter_context(patch.object(runner, "OpenRouterHarness", self.harness))
        self.stack.enter_context(redirect_stdout(io.StringIO()))

    def marker(self, session_id):
        return self.run_dir / "sessions" / session_id / "recovered_tool_pending.json"

    def test_malformed_marker_stops_queued_sessions(self):
        self.marker("waiting").write_text("not JSON")
        with self.assertRaises(json.JSONDecodeError):
            runner.generate(self.run_dir, workers=1, resume=True)
        self.harness.assert_not_called()
        self.assertFalse(any(self.run_dir.glob("sessions/*/result.json")))

    def test_peer_marker_failure_releases_waiter_without_starting_inference(self):
        waiting = self.marker("waiting")
        broken = self.marker("broken")
        waiting.write_text(json.dumps({"status": "running", "monitor_pid": 123456}))
        broken.write_text("not JSON")
        monitor_checked = threading.Event()
        failure_read = threading.Event()
        real_read_text = Path.read_text

        def read_text(path, *args, **kwargs):
            if path == broken:
                if not monitor_checked.wait(2):
                    raise AssertionError("Waiting worker did not check its monitor")
                failure_read.set()
            elif path == waiting and failure_read.is_set():
                # Even completion after a peer failure must not start inference.
                return json.dumps({"status": "completed"})
            return real_read_text(path, *args, **kwargs)

        with patch.object(Path, "read_text", read_text), patch.object(
            runner.os, "kill", side_effect=lambda *_: monitor_checked.set()
        ):
            with self.assertRaises(json.JSONDecodeError):
                runner.generate(self.run_dir, workers=2, resume=True)
        self.harness.assert_not_called()
        self.assertTrue(monitor_checked.is_set())
        self.assertFalse(any(self.run_dir.glob("sessions/*/result.json")))


class ReconciledBudgetTests(unittest.TestCase):
    """All journals, accounting evidence and credentials are temporary fixtures."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.run_dir = Path(self.temporary.name)
        self.credentials = self.run_dir / "fake_credentials.json"
        self.credentials.write_text(json.dumps({"api_key": "offline-placeholder"}))
        self.evidence = self.run_dir / "synthetic_accounting.json"
        self.evidence.write_text('{"note":"offline fixture; no account was queried"}\n')
        self.names = ("first", "second")
        self.reservations = (0.952908, 0.819808)
        for name, reservation in zip(self.names, self.reservations):
            self.write_failed(name, reservation)

    def log_path(self, name):
        return self.run_dir / "sessions" / name / "events.jsonl"

    def events(self, name):
        return [json.loads(line) for line in self.log_path(name).read_text().splitlines()]

    def write_events(self, name, events):
        self.log_path(name).parent.mkdir(parents=True, exist_ok=True)
        self.log_path(name).write_text("".join(json.dumps(event) + "\n" for event in events))

    def append(self, name, event):
        with self.log_path(name).open("a") as stream:
            stream.write(json.dumps(event) + "\n")

    def write_failed(self, name, reservation):
        prompt = "Frozen offline prompt: " + name
        history = [{"role": "user", "content": prompt}]
        terminal = SessionResult(status="uncertain_paid_failure", requests=2, cost_usd=0.1)
        self.write_events(name, [
            {"event": "session_start", "prompt": prompt, "config": asdict(SessionConfig())},
            {"event": "request", "request_index": 0, "max_request_cost_usd": 0.5,
             "payload": {"input": history}},
            {"event": "response", "response": {
                "model": "openai/gpt-5.6-sol", "usage": {"cost": 0.1}, "output": []}},
            {"event": "request", "request_index": 1, "max_request_cost_usd": reservation,
             "payload": {"input": history}},
            {"event": "uncertain_paid_failure", "reserved_cost_retained_usd": reservation,
             "error": "Synthetic transport interruption"},
            {"event": "session_end", "result": asdict(terminal)},
        ])
        (self.log_path(name).parent / "prompt.txt").write_text(prompt)

    def reconcile(self, name, mode="conservative_bound", actual=None):
        harness = OpenRouterHarness(
            api_key="offline-placeholder", sandbox=Mock(), budget=RunBudget(30.0),
            log_path=self.log_path(name),
            transport=Mock(side_effect=AssertionError("No network in accounting tests")),
        )
        prompt = (self.log_path(name).parent / "prompt.txt").read_text()
        bindings = harness.reconciliation_checkpoint(prompt)
        return harness.record_request_reconciliation(
            prompt, reconciliation_id="fixture-" + name, reason="Explicit offline test approval",
            accounting_evidence=[{"path": str(self.evidence),
                                  "sha256": hashlib.sha256(self.evidence.read_bytes()).hexdigest()}],
            charge_resolution=mode, actual_cost_usd=actual,
            retained_cost_upper_usd=(bindings["reserved_cost_retained_usd"]
                                     if mode == "conservative_bound" else None),
            **bindings,
        )

    def run_offline_resume(self, only=None):
        specs = [{"session_id": name, "level": "L1"} for name in self.names]
        with patch.object(runner, "DEFAULT_CREDENTIALS", self.credentials), patch.object(
            runner, "prepare", return_value={"sessions": specs}
        ), patch.object(runner, "PythonSandbox") as sandbox, patch.object(
            runner, "OpenRouterHarness"
        ) as harness, redirect_stdout(io.StringIO()):
            harness.return_value.resume_from_log.return_value = SessionResult(status="budget_exhausted")
            output = runner.generate(self.run_dir, workers=1, resume=True, only=only)
            return output, harness, sandbox

    def test_two_unknown_logs_retain_their_separate_full_reservations(self):
        spent, uncertain = runner.recover_spend(self.run_dir)
        self.assertAlmostEqual(spent, 0.2 + sum(self.reservations))
        self.assertEqual([item["reserved_usd"] for item in uncertain], list(self.reservations))
        self.assertTrue(all(item["blocks_resume"] for item in uncertain))
        self.assertEqual([item["request_index"] for item in uncertain], [1, 1])

    def test_two_conservative_approvals_keep_both_bounds_and_allow_resume(self):
        for name in self.names:
            self.reconcile(name)
        spent, uncertain = runner.recover_spend(self.run_dir)
        self.assertAlmostEqual(spent, 1.972716)
        self.assertEqual(len(uncertain), 2)
        for item in uncertain:
            self.assertFalse(item["blocks_resume"])
            self.assertTrue(item["reconciled_for_resume"])
            self.assertIsNone(item["actual_cost_usd"])
            self.assertEqual(item["reserved_usd"], item["retained_cost_upper_usd"])
        output, harness, _ = self.run_offline_resume()
        self.assertEqual(len(output), 2)
        self.assertEqual(harness.call_count, 2)
        self.assertAlmostEqual(harness.call_args.kwargs["budget"].spent_usd, 1.972716)

    def test_actual_and_held_costs_remain_distinct_in_status(self):
        for name in self.names:
            self.reconcile(name)
        (self.run_dir / "manifest.json").write_text(json.dumps({"sessions": [
            {"session_id": name} for name in self.names]}))
        snapshot = runner.status(self.run_dir)
        self.assertAlmostEqual(snapshot["known_actual_cost_usd"], 0.2)
        self.assertAlmostEqual(snapshot["unresolved_cost_upper_usd"], 1.772716)
        self.assertEqual(snapshot["blocking_unresolved_requests"], 0)

    def test_extra_unresolved_request_globally_blocks_even_selected_approved_session(self):
        for name in self.names:
            self.reconcile(name)
        self.write_events("third", [{"event": "request", "request_index": 0,
                                     "max_request_cost_usd": 0.4}])
        spent, uncertain = runner.recover_spend(self.run_dir)
        self.assertAlmostEqual(spent, 2.372716)
        self.assertEqual(sum(item["blocks_resume"] for item in uncertain), 1)
        with self.assertRaisesRegex(RuntimeError, "Unresolved model requests"):
            self.run_offline_resume(only="first")

    def test_only_one_approved_failure_still_blocks_the_other(self):
        self.reconcile("first")
        with self.assertRaisesRegex(RuntimeError, "Unresolved model requests"):
            self.run_offline_resume()

    def test_authoritative_zero_releases_only_its_own_reservation(self):
        self.reconcile("first", mode="authoritative_cost", actual=0.0)
        spent, uncertain = runner.recover_spend(self.run_dir)
        self.assertAlmostEqual(spent, 0.2 + self.reservations[1])
        self.assertEqual(len(uncertain), 1)
        self.assertEqual(Path(uncertain[0]["log"]).parent.name, "second")

    def test_authoritative_nonzero_replaces_bound_with_actual_cost(self):
        self.reconcile("first", mode="authoritative_cost", actual=0.03)
        spent, _ = runner.recover_spend(self.run_dir)
        self.assertAlmostEqual(spent, 0.23 + self.reservations[1])

    def test_duplicate_reconciliation_cannot_release_twice(self):
        event = self.reconcile("first", mode="authoritative_cost", actual=0.0)
        self.append("first", event)
        with self.assertRaises(ValueError):
            runner.recover_spend(self.run_dir)

    def test_wrong_request_index_or_retained_amount_cannot_reconcile(self):
        event = self.reconcile("first")
        original = self.events("first")
        for key, value in (("request_index", 0), ("retained_cost_upper_usd", 0.01)):
            with self.subTest(field=key):
                modified = dict(event)
                modified[key] = value
                self.write_events("first", original[:-1] + [modified])
                with self.assertRaises(ValueError):
                    runner.recover_spend(self.run_dir)

    def test_reconciliation_from_another_log_cannot_transfer_credit(self):
        event = self.reconcile("first")
        self.append("second", event)
        with self.assertRaises(ValueError):
            runner.recover_spend(self.run_dir)

    def test_missing_or_changed_evidence_blocks_recovery(self):
        event = self.reconcile("first")
        original = self.events("first")
        event["accounting_evidence"] = []
        self.write_events("first", original[:-1] + [event])
        with self.assertRaises(ValueError):
            runner.recover_spend(self.run_dir)
        self.write_events("first", original)
        self.evidence.write_text("changed after approval")
        with self.assertRaises(ValueError):
            runner.recover_spend(self.run_dir)

    def test_later_success_does_not_clear_earlier_conservative_bound(self):
        self.reconcile("first")
        self.append("first", {"event": "request", "request_index": 2,
                              "max_request_cost_usd": 0.6, "payload": {"input": []}})
        self.append("first", {"event": "response", "response": {"usage": {"cost": 0.07}}})
        spent, uncertain = runner.recover_spend(self.run_dir)
        self.assertAlmostEqual(spent, 0.27 + sum(self.reservations))
        first = next(item for item in uncertain if Path(item["log"]).parent.name == "first")
        self.assertEqual(first["request_index"], 1)
        self.assertFalse(first["blocks_resume"])
        self.assertEqual(first["reserved_usd"], self.reservations[0])


if __name__ == "__main__":
    unittest.main()
