"""Checks of paid-request accounting and simulator/source boundary only."""
import json
from pathlib import Path
import tempfile
import unittest

from .baek_perishable import (BudgetExceeded, DurableBudget, build_prelude, make_prompt,
                             atomic_json, resolve_budget_directory, DEFAULT_RUN)


class BudgetTests(unittest.TestCase):
    def test_unresolved_reservation_survives_restart_and_caps_spend(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = DurableBudget(directory)
            budget.reserve(2.)
            budget.settle(2., 0.75)
            budget.reserve(4.)
            budget.settle(4., None)
            recovered = DurableBudget(directory)
            self.assertEqual((recovered.spent_usd, recovered.reserved_usd), (0.75, 4.))
            with self.assertRaises(BudgetExceeded):
                recovered.reserve(7.2501)

    def test_reply_written_before_crash_reconciles_only_exact_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = DurableBudget(directory)
            budget.reserve(3.)
            request_id = budget.current_reservation_id()
            log = Path(directory) / "extended/sessions/l2_r1/events.jsonl"
            log.parent.mkdir(parents=True)
            events = [dict(event="request", budget_reservation_id=request_id),
                      dict(event="response", response={"usage": {"cost": 0.4}})]
            log.write_text("".join(json.dumps(event) + "\n" for event in events))
            recovered = DurableBudget(directory)
            self.assertEqual(recovered.spent_usd, 0.4)
            self.assertEqual(recovered.reserved_usd, 0.)

    def test_unlogged_reserved_request_remains_fully_held(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = DurableBudget(directory)
            budget.reserve(1.5)
            recovered = DurableBudget(directory)
            self.assertEqual(recovered.reserved_usd, 1.5)

    def test_nested_resume_reuses_saved_budget_and_rejects_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            extended = root / "extended"
            extended.mkdir()
            target = extended / "budget_allocation.json"
            atomic_json(target, dict(global_budget_directory=str(root), global_shared_limit_usd=12.))
            original = target.read_bytes()
            self.assertEqual(resolve_budget_directory(extended), root)
            self.assertEqual(resolve_budget_directory(extended, root), root)
            with self.assertRaises(ValueError):
                resolve_budget_directory(extended, extended)
            self.assertEqual(target.read_bytes(), original)
            self.assertFalse((extended / "budget.json").exists())

    def test_actual_extended_location_cannot_request_own_pool(self):
        self.assertEqual(resolve_budget_directory(DEFAULT_RUN / "extended"), DEFAULT_RUN.resolve())
        with self.assertRaises(ValueError):
            resolve_budget_directory(DEFAULT_RUN / "extended", DEFAULT_RUN / "extended")


class SourceTests(unittest.TestCase):
    def test_prelude_omits_test_data_and_primary_grid(self):
        source = build_prelude()
        compile(source, "trusted_helper.py", "exec")
        self.assertNotIn("def scenarios(", source)
        for holdout_seed in ("17092001", "17094001"):
            self.assertNotIn(holdout_seed, source + make_prompt())
        self.assertIn("17091001", source)


if __name__ == "__main__":
    unittest.main()
