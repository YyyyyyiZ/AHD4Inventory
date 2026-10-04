"""All transports are mocks; credentials and ledgers exist only in temp dirs."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal
import json
import multiprocessing
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
from unittest.mock import patch

from .model_comparison_client import (
    BudgetExceeded, ClientConfig, ClientError, ConfigurationError, CredentialError,
    DurableDollarLedger, FrozenPricing, ModelComparisonClient, ResponseError,
    estimate_charge, extract_code_only, token_usage,
)


def process_reserve(directory, gate, queue):
    ledger = DurableDollarLedger(directory, "1")
    ledger.register("shared", {"mock": True})
    gate.wait(10)
    try:
        ledger.reserve("shared", ".3", request_metadata={})
        queue.put("reserved")
    except BudgetExceeded:
        queue.put("blocked")


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="model_client_mock_")
        self.root = Path(self.tmp.name)
        self.credential = self.root / "external_credentials.json"
        self.keys = ("mock-key-first-not-real", "mock-key-second-not-real")
        self.credential.write_text(json.dumps({"credentials": [
            {"api_key": key, "allowed_origin": "https://provider.invalid"} for key in self.keys]}))
        self.credential.chmod(0o600)
        self.config = ClientConfig("test", "https://provider.invalid/v1/chat/completions", "mock-model",
                                   FrozenPricing("1.32", ".044", "3.96"), endpoint_confirmed=True,
                                   thinking_enabled=True, reasoning_effort="max")
        self.messages = [{"role": "user", "content": "Write a Python ordering function."}]
        self.calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def response(self, **changes):
        result = {"id": "mock-generation", "model": "mock-model",
            "usage": {"prompt_tokens": 100, "prompt_cache_hit_tokens": 80, "prompt_cache_miss_tokens": 20,
                      "completion_tokens": 50, "completion_tokens_details": {"reasoning_tokens": 30}},
            "choices": [{"finish_reason": "stop", "message": {
                "content": "<think>PRIVATE_HIDDEN_REASONING</think>\nHere is code:\n```python\ndef policy(x):\n    return x\n```",
                "reasoning_content": "PRIVATE_HIDDEN_REASONING"}}]}
        result.update(changes)
        return result

    def client(self, response=None, *, config=None, directory=None, index=0, limit="1", transport=None):
        def mock(**kwargs):
            self.calls.append(kwargs)
            return response if response is not None else self.response()
        return ModelComparisonClient(config or self.config, directory or self.root / "ledger", limit,
                                     self.credential, index, transport=transport or mock)

    def records(self, directory=None):
        return json.loads(((directory or self.root / "ledger") / "budget.json").read_text())["requests"]

    def test_peak_estimate_cached_counts_and_reasoning_not_double_counted(self):
        client = self.client()
        code, info = client.chat(self.messages, max_tokens=200)
        expected = (Decimal(80) * Decimal(".044") + Decimal(20) * Decimal("1.32") + Decimal(50) * Decimal("3.96")) / Decimal(1_000_000)
        self.assertEqual(info["cost_status"], "pricing_upper_estimate")
        self.assertEqual(Decimal(str(info["estimated_upper_usd"])), expected)
        self.assertIsNone(info["actual_cost_usd"])
        self.assertEqual(info["usage"]["billed_output_tokens"], 50)
        self.assertEqual(info["requested_reasoning_effort"], "max")
        self.assertEqual(self.calls[0]["payload"]["thinking"], {"type": "enabled"})
        self.assertEqual(self.calls[0]["payload"]["reasoning_effort"], "max")
        self.assertEqual(code, "```python\ndef policy(x):\n    return x\n```")
        self.assertEqual(client.summary()["held_upper_usd"], 0)
        for path in (self.root / "ledger").rglob("*.json"):
            text = path.read_text()
            self.assertNotIn("PRIVATE_HIDDEN_REASONING", text)
            for key in self.keys:
                self.assertNotIn(key, text)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_actual_cost_takes_precedence(self):
        response = self.response()
        response["usage"]["cost"] = .00005
        client = self.client(response)
        _, info = client.chat(self.messages, max_tokens=200)
        self.assertEqual(info["cost_status"], "actual")
        self.assertEqual(info["actual_cost_usd"], .00005)
        self.assertIsNone(info["estimated_upper_usd"])
        self.assertEqual(client.summary()["actual_cost_usd"], .00005)

    def test_separate_reasoning_and_missing_cache_upper_price(self):
        price, usage = estimate_charge({"prompt_tokens": 100, "completion_tokens": 20,
            "completion_tokens_details": {"reasoning_tokens": 30}}, self.config.pricing, completion_includes_reasoning=False)
        self.assertEqual(usage["billed_output_tokens"], 50)
        self.assertFalse(usage["cache_counts_reported"])
        self.assertEqual(price, Decimal(".00033"))
        _, usage = estimate_charge({"input_tokens": 100, "input_tokens_details": {"cached_tokens": 90},
                                   "output_tokens": 50}, self.config.pricing)
        self.assertEqual(usage["prompt_cache_miss_tokens"], 10)
        with self.assertRaises(ResponseError):
            token_usage({"prompt_tokens": 100, "completion_tokens": 20}, completion_includes_reasoning=False)

    def test_unconfirmed_or_live_network_disabled_never_reads_credentials_or_posts(self):
        config = replace(self.config, endpoint_confirmed=False)
        client = self.client(config=config)
        self.credential.unlink()
        with self.assertRaisesRegex(ConfigurationError, "unconfirmed"):
            client.chat(self.messages)
        self.assertEqual(client.summary()["requests"], 0)
        live = ModelComparisonClient(self.config, self.root / "ledger2", 1, self.credential)
        with patch("urllib.request.build_opener", side_effect=AssertionError("must not reach network")):
            with self.assertRaisesRegex(ConfigurationError, "disabled"):
                live.chat(self.messages)
        self.assertFalse(self.calls)

    def test_unknown_transport_charge_held_no_retry_no_key_rotation(self):
        def failure(**kwargs):
            self.calls.append(kwargs)
            raise urllib.error.HTTPError(kwargs["endpoint"], 429, self.keys[1], {}, None)
        client = self.client(index=1, transport=failure)
        with self.assertRaises(ClientError) as caught:
            client.chat(self.messages, max_tokens=200)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0]["api_key"], self.keys[1])
        self.assertNotIn(self.keys[1], str(caught.exception))
        record = next(iter(self.records().values()))
        self.assertEqual(record["state"], "unknown_charge")
        self.assertEqual(record["http_status"], 429)
        self.assertGreater(client.summary()["held_upper_usd"], 0)
        with self.assertRaises(ConfigurationError):
            self.client(index=0)

    def test_invalid_usage_preserves_reservation(self):
        client = self.client(self.response(usage={"prompt_tokens": 100, "completion_tokens": 50,
                                               "prompt_cache_hit_tokens": 90, "prompt_cache_miss_tokens": 90}))
        with self.assertRaises(ResponseError):
            client.chat(self.messages, max_tokens=200)
        self.assertEqual(next(iter(self.records().values()))["state"], "unknown_charge")
        self.assertGreater(client.summary()["held_upper_usd"], 0)

    def test_invalid_code_billed_once_and_hidden_reasoning_dropped(self):
        response = self.response()
        response["choices"][0]["message"]["content"] = "<think>PRIVATE_HIDDEN_REASONING"
        client = self.client(response)
        with self.assertRaises(ResponseError):
            client.chat(self.messages, max_tokens=200)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(client.summary()["held_upper_usd"], 0)
        self.assertGreater(client.summary()["estimated_upper_usd"], 0)
        receipt = next((self.root / "ledger/requests").glob("*/response.json")).read_text()
        self.assertNotIn("PRIVATE_HIDDEN_REASONING", receipt)
        self.assertIsNone(json.loads(receipt)["content"])

    def test_two_code_blocks_and_bare_code(self):
        text, sources = extract_code_only("```python\ndef a():\n return 1\n```\n```python\ndef b():\n return 2\n```")
        self.assertEqual(len(sources), 2)
        self.assertEqual(text.count("```python"), 2)
        self.assertEqual(len(extract_code_only("def a():\n return 1")[1]), 1)
        for invalid in ("Sure", "```python\ndef broken(\n```", "<think>do not expose"):
            with self.assertRaises(ResponseError):
                extract_code_only(invalid)

    def test_model_alias_recorded_and_unexpected_model_pauses(self):
        config = replace(self.config, allowed_returned_models=("mock-model-version",))
        client = self.client(self.response(model="mock-model-version"), config=config)
        _, info = client.chat(self.messages, max_tokens=200)
        self.assertEqual(info["returned_model"], "mock-model-version")
        other = self.client(self.response(model="wrong-model"), directory=self.root / "other")
        with self.assertRaises(ResponseError):
            other.chat(self.messages, max_tokens=200)
        self.assertIsNotNone(other.summary()["paused_reason"])
        self.assertGreater(other.summary()["held_upper_usd"], 0)
        with self.assertRaises(BudgetExceeded):
            other.chat(self.messages, max_tokens=200)

    def test_multiple_models_share_limit_and_frozen_prices(self):
        first = self.client()
        second = self.client(config=replace(self.config, client_id="cheap", model="cheap-model"))
        self.assertEqual(first.ledger.path, second.ledger.path)
        for client in (first, second):
            client.ledger.reserve(client.config.client_id, ".4", request_metadata={})
        with self.assertRaises(BudgetExceeded):
            first.ledger.reserve("test", ".21", request_metadata={})
        self.assertEqual(first.summary()["committed_upper_usd"], .8)
        with self.assertRaises(ConfigurationError):
            self.client(limit="2")
        with self.assertRaises(ConfigurationError):
            self.client(config=replace(self.config, pricing=FrozenPricing("2", "1", "3")))

    def test_thread_atomic_reservations(self):
        ledger = DurableDollarLedger(self.root / "threaded", "1")
        ledger.register("shared", {"mock": True})
        gate = threading.Barrier(12)
        def one(_):
            own = DurableDollarLedger(self.root / "threaded", "1")
            gate.wait(10)
            try:
                own.reserve("shared", ".3", request_metadata={})
                return True
            except BudgetExceeded:
                return False
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(one, range(12)))
        self.assertEqual(sum(results), 3)
        self.assertEqual(ledger.summary()["committed_upper_usd"], .9)

    def test_process_atomic_reservations(self):
        context = multiprocessing.get_context("spawn")
        gate, queue = context.Event(), context.Queue()
        directory = self.root / "multiprocess"
        processes = [context.Process(target=process_reserve, args=(directory, gate, queue)) for _ in range(6)]
        for process in processes:
            process.start()
        gate.set()
        try:
            results = [queue.get(timeout=20) for _ in processes]
            for process in processes:
                process.join(20)
                self.assertEqual(process.exitcode, 0)
            self.assertEqual(results.count("reserved"), 3)
            self.assertEqual(DurableDollarLedger(directory, "1").summary()["committed_upper_usd"], .9)
        finally:
            for process in processes:
                if process.is_alive():
                    process.kill()
                    process.join()

    def test_external_0600_origin_bound_credential(self):
        client = self.client()
        self.credential.chmod(0o644)
        with self.assertRaises(CredentialError):
            client.chat(self.messages)
        self.credential.chmod(0o600)
        data = json.loads(self.credential.read_text())
        data["credentials"][0]["allowed_origin"] = "https://another.invalid"
        self.credential.write_text(json.dumps(data))
        with self.assertRaises(CredentialError):
            client.chat(self.messages)
        self.assertEqual(client.summary()["requests"], 0)
        self.assertFalse(self.calls)

    def test_extra_provider_body_frozen_and_cannot_override_core(self):
        extra = {"provider": {"require_parameters": True, "allow_fallbacks": False,
                              "max_price": {"prompt": 4, "completion": 15, "request": 0}}}
        config = replace(self.config, extra_body=extra, reasoning_parameter="reasoning")
        client = self.client(config=config)
        extra["provider"]["allow_fallbacks"] = True
        client.chat(self.messages, max_tokens=200)
        self.assertFalse(self.calls[0]["payload"]["provider"]["allow_fallbacks"])
        self.assertEqual(self.calls[0]["payload"]["reasoning"], {"effort": "max"})
        for field in ("model", "messages", "max_tokens", "max_completion_tokens", "thinking", "reasoning", "stream", "tools", "n"):
            with self.assertRaises(ConfigurationError):
                replace(self.config, extra_body={field: "forbidden"}).identity()

    def test_cost_exceeding_reserve_is_recorded_then_pauses(self):
        response = self.response()
        response["usage"]["cost"] = .9
        client = self.client(response)
        with self.assertRaises(ResponseError):
            client.chat(self.messages, max_tokens=200)
        self.assertEqual(client.summary()["actual_cost_usd"], .9)
        self.assertIsNotNone(client.summary()["paused_reason"])
        with self.assertRaises(BudgetExceeded):
            client.chat(self.messages, max_tokens=200)
        self.assertEqual(len(self.calls), 1)

    def test_malformed_choices_known_fee_is_not_lost(self):
        response = self.response(choices={"unexpected": "shape"}, usage={"cost": .00005})
        client = self.client(response)
        with self.assertRaises(ResponseError):
            client.chat(self.messages, max_tokens=200)
        self.assertEqual(client.summary()["actual_cost_usd"], .00005)

    def test_truncated_response_is_charged_without_automatic_retry(self):
        response = self.response()
        response["choices"][0]["finish_reason"] = "length"
        client = self.client(response)
        with self.assertRaises(ResponseError):
            client.chat(self.messages, max_tokens=200)
        self.assertEqual(len(self.calls), 1)
        self.assertGreater(client.summary()["estimated_upper_usd"], 0)

    def test_missing_usage_and_invalid_cost_hold_full_reservation(self):
        for index, usage in enumerate(({}, {"cost": -1, "prompt_tokens": 100, "completion_tokens": 50})):
            client = self.client(self.response(usage=usage), directory=self.root / f"bad_{index}")
            with self.assertRaises(ResponseError):
                client.chat(self.messages, max_tokens=200)
            self.assertGreater(client.summary()["held_upper_usd"], 0)
            self.assertEqual(client.summary()["estimated_upper_usd"], 0)

    def test_completion_cap_can_use_openai_parameter_and_includes_reasoning(self):
        client = self.client(config=replace(self.config, max_tokens_parameter="max_completion_tokens"))
        preview = client.preview(self.messages, max_tokens=200)
        self.assertEqual(preview["payload"]["max_completion_tokens"], 200)
        self.assertNotIn("max_tokens", preview["payload"])
        with self.assertRaises(ConfigurationError):
            replace(self.config, output_limit_includes_reasoning=False).identity()
        with self.assertRaises(ConfigurationError):
            replace(self.config, thinking_enabled=1).identity()


if __name__ == "__main__":
    unittest.main()
