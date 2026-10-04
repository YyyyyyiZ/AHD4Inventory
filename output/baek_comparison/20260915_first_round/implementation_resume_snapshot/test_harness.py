"""Network-free synthetic checks for paid-call accounting and OS isolation."""
import json
import io
from dataclasses import asdict
import os
from pathlib import Path
import tempfile
import unittest
import urllib.error

try:
    from .harness import OpenRouterHarness, RunBudget, SessionConfig, UnresolvedRequestError
    from .sandbox import PythonSandbox, SandboxResult
except ImportError:
    from harness import OpenRouterHarness, RunBudget, SessionConfig, UnresolvedRequestError
    from sandbox import PythonSandbox, SandboxResult


class MockSandbox:
    def probe(self):
        return None

    def run(self, code, timeout_seconds):
        assert code == "print(2)"
        return SandboxResult("2\n", "", 0, 0.1)


def response(output, cost=0.01):
    return {"model": "openai/gpt-5.6-sol-2026-08-01", "status": "completed", "output": output,
            "usage": {"cost": cost, "input_tokens": 100, "output_tokens": 50, "total_tokens": 150}}


class HarnessTests(unittest.TestCase):
    def test_continuation_preserves_reasoning_and_removes_exhausted_tools(self):
        seen = []
        reasoning = {"type": "reasoning", "id": "rs_1", "encrypted_content": "opaque", "summary": []}
        def transport(payload, key):
            seen.append(json.loads(json.dumps(payload)))
            if len(seen) == 1:
                return response([reasoning, {"type": "function_call", "id": "fc_1", "call_id": "call_1",
                                            "name": "run_python", "arguments": '{"code":"print(2)"}'}])
            return response([{"type": "message", "role": "assistant", "content": [
                {"type": "output_text", "text": "```python\ndef compute_order_amount(on_hand_inventory, pipeline_orders):\n    return 0.0\n```"}]}])
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "calls.jsonl"
            budget = RunBudget(1)
            h = OpenRouterHarness(api_key="test-secret-key", sandbox=MockSandbox(), budget=budget,
                                  log_path=log, config=SessionConfig(max_tool_calls=1), transport=transport)
            result = h.run("Synthetic test-secret-key")
            self.assertEqual(result.status, "completed")
            self.assertEqual(result.requests, 2)
            self.assertEqual(result.tool_calls, 1)
            self.assertAlmostEqual(budget.spent_usd, 0.02)
            self.assertIn(reasoning, seen[1]["input"])
            self.assertNotIn("tools", seen[1])
            self.assertNotIn("test-secret-key", log.read_text())
            self.assertEqual(seen[0]["provider"]["allow_fallbacks"], False)
            self.assertNotIn("parallel_tool_calls", seen[0])
            self.assertEqual(seen[0]["max_output_tokens"], 16384)

    def test_unknown_paid_failure_keeps_reservation_and_never_retries(self):
        calls = []
        def transport(payload, key):
            calls.append(payload)
            raise TimeoutError("synthetic failure")
        with tempfile.TemporaryDirectory() as tmp:
            budget = RunBudget(1)
            result = OpenRouterHarness(api_key="test-key", sandbox=MockSandbox(), budget=budget,
                                      log_path=Path(tmp)/"log", transport=transport).run("test")
            self.assertEqual(result.status, "uncertain_paid_failure")
            self.assertEqual(len(calls), 1)
            self.assertGreater(budget.spent_usd, 0)
            self.assertEqual(budget.reserved_usd, 0)

    def test_budget_stops_before_transport(self):
        def forbidden(*args):
            raise AssertionError("Transport must not be called")
        with tempfile.TemporaryDirectory() as tmp:
            result = OpenRouterHarness(api_key="test-key", sandbox=MockSandbox(), budget=RunBudget(0.001),
                                      log_path=Path(tmp)/"log", transport=forbidden).run("test")
            self.assertEqual(result.status, "budget_exhausted")
            self.assertEqual(result.requests, 0)

    def test_wrong_model_stops(self):
        def transport(payload, key):
            out = response([])
            out["model"] = "another-model"
            return out
        with tempfile.TemporaryDirectory() as tmp:
            result = OpenRouterHarness(api_key="test-key", sandbox=MockSandbox(), budget=RunBudget(1),
                                      log_path=Path(tmp)/"log", transport=transport).run("test")
            self.assertEqual(result.status, "unexpected_model")

    def test_http_rejection_logs_redacted_body_and_releases_reservation(self):
        calls = []
        def transport(payload, key):
            calls.append(payload)
            body = {"error": {"message": "No endpoints found that can handle the requested parameters test-secret-key",
                              "metadata": {"failed_routing_step": "Filter by Parameters"}},
                    "openrouter_metadata": {"attempt": 0, "endpoints": {"available": [{"selected": False}]}}}
            raise urllib.error.HTTPError("https://openrouter.ai/api/v1/responses", 404, "Not Found", {},
                                         io.BytesIO(json.dumps(body).encode()))
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp)/"log"
            budget = RunBudget(1)
            result = OpenRouterHarness(api_key="test-secret-key", sandbox=MockSandbox(), budget=budget,
                                      log_path=log, transport=transport).run("test")
            self.assertEqual(result.status, "transport_rejected")
            self.assertEqual(result.http_status, 404)
            self.assertEqual(len(calls), 1)
            self.assertEqual(budget.spent_usd, 0)
            self.assertEqual(budget.reserved_usd, 0)
            self.assertNotIn("test-secret-key", log.read_text())
            rejection = next(e for e in map(json.loads, log.read_text().splitlines()) if e["event"] == "request_rejected")
            self.assertIn("No endpoints found", rejection["error_body"]["error"]["message"])

    def test_unknown_http_404_keeps_reservation(self):
        def transport(payload, key):
            raise urllib.error.HTTPError("https://openrouter.ai/api/v1/responses", 404, "Not Found", {},
                                         io.BytesIO(b'{"error":{"message":"unknown upstream failure"}}'))
        with tempfile.TemporaryDirectory() as tmp:
            budget = RunBudget(1)
            result = OpenRouterHarness(api_key="test-key", sandbox=MockSandbox(), budget=budget,
                                      log_path=Path(tmp)/"log", transport=transport).run("test")
            self.assertEqual(result.status, "uncertain_paid_failure")
            self.assertGreater(budget.spent_usd, 0)

    def test_http_server_error_keeps_reservation(self):
        def transport(payload, key):
            raise urllib.error.HTTPError("https://openrouter.ai/api/v1/responses", 503, "Unavailable", {},
                                         io.BytesIO(b'{"error":{"message":"synthetic upstream error"}}'))
        with tempfile.TemporaryDirectory() as tmp:
            budget = RunBudget(1)
            result = OpenRouterHarness(api_key="test-key", sandbox=MockSandbox(), budget=budget,
                                      log_path=Path(tmp)/"log", transport=transport).run("test")
            self.assertEqual(result.status, "uncertain_paid_failure")
            self.assertEqual(result.http_status, 503)
            self.assertGreater(budget.spent_usd, 0)


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run_dir = Path(self.temp.name)
        self.log = self.run_dir / "sessions/synthetic/events.jsonl"
        self.log.parent.mkdir(parents=True)
        self.prompt = "Frozen synthetic prompt"
        self.config = SessionConfig()
        self.reasoning = {"type": "reasoning", "id": "rs_saved", "encrypted_content": "saved-encrypted", "summary": []}
        self.call = {"type": "function_call", "id": "fc_saved", "call_id": "call_saved",
                     "name": "run_python", "arguments": '{"code":"print(2)"}'}
        self.initial = [{"role": "user", "content": self.prompt}]
        self.events = [{"event": "session_start", "prompt": self.prompt, "config": asdict(self.config)},
                       {"event": "request", "request_index": 0, "max_request_cost_usd": 0.5,
                        "payload": {"input": self.initial}},
                       {"event": "response", "response": response([self.reasoning, self.call])}]
        self.final = response([{"type": "message", "role": "assistant", "content": [
            {"type": "output_text", "text": "```python\ndef compute_order_amount(on_hand_inventory, pipeline_orders):\n    return 0.0\n```"}]}])

    def write_log(self):
        self.log.write_text("".join(json.dumps(event) + "\n" for event in self.events))

    def test_pending_tool_runs_before_exact_continuation_without_repeating_response(self):
        self.write_log()
        sequence = []
        outer = self
        class Sandbox(MockSandbox):
            def run(self, code, timeout_seconds):
                sequence.append("tool")
                return super().run(code, timeout_seconds)
        def transport(payload, key):
            sequence.append("api")
            outer.assertEqual(payload["input"][:3], outer.initial + [outer.reasoning, outer.call])
            outer.assertEqual(payload["input"][3]["call_id"], "call_saved")
            return outer.final
        result = OpenRouterHarness(api_key="synthetic-key", sandbox=Sandbox(), budget=RunBudget(1, 0.01),
                                  log_path=self.log, transport=transport).resume_from_log(self.prompt)
        self.assertEqual(sequence, ["tool", "api"])
        self.assertEqual(result.requests, 2)
        self.assertEqual(result.tool_calls, 1)
        self.assertAlmostEqual(result.python_seconds, 0.1)
        self.assertAlmostEqual(result.cost_usd, 0.02)
        self.assertEqual(result.usage["input_tokens"], 200)

    def test_recovered_ram_tool_is_never_reexecuted_and_pause_is_not_charged(self):
        tool_result = {"stdout": "recovered from RAM", "stderr": "", "returncode": 0,
                       "elapsed_seconds": 2.5, "timed_out": False, "remaining_calls": 49,
                       "remaining_seconds": 3597.5}
        self.events.extend([{"event": "session_paused", "paused_seconds": 10000},
                            {"event": "tool_result", "call": self.call, "result": tool_result}])
        self.write_log()
        class Sandbox(MockSandbox):
            def run(self, *args):
                raise AssertionError("Recovered tool must not execute again")
        seen = []
        def transport(payload, key):
            seen.append(json.loads(json.dumps(payload)))
            return self.final
        result = OpenRouterHarness(api_key="synthetic-key", sandbox=Sandbox(), budget=RunBudget(1, 0.01),
                                  log_path=self.log, transport=transport).resume_from_log(self.prompt)
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0]["input"][-1]["output"], json.dumps(tool_result))
        self.assertEqual(result.python_seconds, 2.5)
        self.assertEqual(result.tool_calls, 1)

    def test_final_response_checkpoint_returns_without_any_api_or_tool(self):
        self.events[-1]["response"] = self.final
        self.write_log()
        class Sandbox:
            def probe(self):
                raise AssertionError("Final checkpoint needs no execution")
        def forbidden(*args):
            raise AssertionError("Final checkpoint needs no API")
        result = OpenRouterHarness(api_key="synthetic-key", sandbox=Sandbox(), budget=RunBudget(1, 0.01),
                                  log_path=self.log, transport=forbidden).resume_from_log(self.prompt)
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.requests, 1)
        self.assertTrue(result.final_code)

    def test_unknown_api_refuses_then_explicit_interruption_counts_charge_once(self):
        try:
            from .runner import recover_spend
        except ImportError:
            from runner import recover_spend
        self.events.pop()
        self.write_log()
        seen = []
        def transport(payload, key):
            seen.append(payload)
            return self.final
        harness = OpenRouterHarness(api_key="synthetic-key", sandbox=MockSandbox(), budget=RunBudget(2, 0.5),
                                    log_path=self.log, transport=transport)
        with self.assertRaises(UnresolvedRequestError):
            harness.resume_from_log(self.prompt)
        self.assertEqual(seen, [])
        self.assertAlmostEqual(recover_spend(self.run_dir)[0], 0.5)
        harness.record_request_interruption(self.prompt, interruption_id="synthetic-pause-1", reason="Explicitly reconciled lost response")
        self.assertEqual(seen, [])
        self.assertAlmostEqual(recover_spend(self.run_dir)[0], 0.5)
        result = harness.resume_from_log(self.prompt)
        self.assertEqual(len(seen), 1)
        self.assertEqual(result.requests, 2)
        self.assertEqual(result.uncertain_cost_usd, 0.5)
        self.assertAlmostEqual(recover_spend(self.run_dir)[0], 0.51)

    def test_prompt_change_and_duplicate_tool_completion_are_rejected(self):
        self.write_log()
        harness = OpenRouterHarness(api_key="synthetic-key", sandbox=MockSandbox(), budget=RunBudget(1, 0.01),
                                    log_path=self.log, transport=lambda *_: self.final)
        with self.assertRaises(ValueError):
            harness.resume_from_log("different prompt")
        tool = {"event": "tool_result", "call": self.call, "result": {"elapsed_seconds": 1}}
        self.events.extend([tool, tool])
        self.write_log()
        with self.assertRaises(ValueError):
            harness.resume_from_log(self.prompt)


class SandboxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[3]
        cls.sandbox = PythonSandbox(str(root / ".venv/bin/python"))

    def test_actual_os_isolation_and_numeric_libraries(self):
        result = self.sandbox.probe()
        self.assertEqual(result.returncode, 0)

    def test_private_file_environment_and_fresh_process(self):
        with tempfile.NamedTemporaryFile(prefix="baek-private-canary-") as f:
            f.write(b"private canary"); f.flush()
            code = (f"try:\n open({f.name!r}).read()\nexcept PermissionError:\n print('denied')\n"
                    "else:\n raise AssertionError('private external file accessible')\n"
                    "import os\nassert 'OPENROUTER_API_KEY' not in os.environ\n"
                    "open('fresh-only.txt','w').write('test')\n")
            old = os.environ.get("OPENROUTER_API_KEY")
            os.environ["OPENROUTER_API_KEY"] = "synthetic-parent-secret"
            try:
                result = self.sandbox.run(code, 5)
            finally:
                if old is None:
                    os.environ.pop("OPENROUTER_API_KEY", None)
                else:
                    os.environ["OPENROUTER_API_KEY"] = old
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "denied")
            result = self.sandbox.run("import os; assert not os.path.exists('fresh-only.txt'); print('fresh')", 5)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_timeout_and_output_capture(self):
        result = self.sandbox.run("while True: pass", 0.25)
        self.assertTrue(result.timed_out)
        result = self.sandbox.run("print('a'*100000)", 5, max_output_bytes=120000)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(result.stdout), 100001)


if __name__ == "__main__":
    unittest.main()
