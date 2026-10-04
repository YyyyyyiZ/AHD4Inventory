"""Tiny offline report fixtures; no generated policy or real test tape is run."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from .analysis_report import report, load_evaluations


SID = "exp_iid_fixed6"


def _save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj))


def _manifest(root):
    _save(root / "dataset_manifest.json", {"files": [{"scenario_id": SID, "split": "test", "n_paths": 3, "arrays_sha256": "a" * 64}]})


def _evaluation(root, policy_id, costs, *, family="self_evolve", repeat=1, full=True,
                windows=(("steady", 200),), training_horizon=200, demand=None):
    arrays, rows = {}, []
    directory = root / "evaluation" / SID / policy_id
    directory.mkdir(parents=True, exist_ok=True)
    demand = np.array([1000.1, 2000.2, 3000.3]) if demand is None else np.array(demand)
    for mode, horizon in windows:
        prefix = f"{mode}_h{horizon}"
        values = {"total_cost": np.array(costs) * horizon, "holding_cost": np.array(costs) * horizon,
                  "lost_units": np.zeros(3), "demand_units": demand, "sales_units": demand, "order_units": np.full(3, 50 * horizon)}
        arrays.update({prefix + "_" + name: value for name, value in values.items()})
        rows.append(dict(scenario_id=SID, policy_id=policy_id, family=family, repeat=repeat, full_protocol=full,
                         split="test", mode=mode, horizon=horizon, source_training_horizon=training_horizon,
                         costs_path=str((directory / "paths.npz").relative_to(root)), array_prefix=prefix,
                         mean_cost_per_period=float(np.mean(costs)), holding_per_period=float(np.mean(costs)),
                         lost_units_per_period=0., fill_rate=1., orders_per_period=50.,
                         dataset_arrays_sha256="a" * 64, code_sha256=str(repeat or 0) * 64))
    np.savez_compressed(directory / "paths.npz", **arrays)
    _save(directory / "test.json", rows)
    return directory / "test.json"


def _csv(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        _manifest(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def run_report(self):
        return report(self.root, n_bootstrap=40, make_plots=False)

    def test_empty_is_explicitly_incomplete_with_eighteen_planned(self):
        result = self.run_report()
        self.assertFalse(result["complete"])
        self.assertEqual(result["expected_primary_runs"], 18)
        self.assertEqual(result["primary_h200_available"], 0)
        self.assertEqual(len(result["coverage"]), 18)
        self.assertIn("尚未完成", (self.root / "report.md").read_text())

    def test_pilot_and_horizon_extension_do_not_fill_main_denominator(self):
        _evaluation(self.root, "self_evolve_h200_r1", [1, 2, 3], full=False)
        _evaluation(self.root, "self_evolve_h50_r2", [1, 2, 3], repeat=2, training_horizon=50)
        result = self.run_report()
        self.assertEqual(result["primary_h200_available"], 0)
        self.assertEqual(result["pilot_or_nonprimary_rows"], 1)
        self.assertEqual(result["extension_rows"], 1)

    def test_three_repeat_mean_sample_sd_and_path_average_pairing(self):
        _evaluation(self.root, "baseline_h200_constant_order", [20, 30, 40], family="constant_order", repeat=None)
        for repeat in (1, 2, 3):
            _evaluation(self.root, f"self_evolve_h200_r{repeat}", [8+2*repeat, 18+2*repeat, 28+2*repeat], repeat=repeat)
        result = self.run_report()
        self.assertEqual(result["primary_h200_available"], 3)
        self.assertEqual(result["paired_rows"], 4)
        self.assertEqual(result["issues"], [])
        repeats = _csv(self.root / "tables/repeats.csv")
        self.assertEqual(float(repeats[0]["mean_cost_per_period_mean"]), 22.)
        self.assertEqual(float(repeats[0]["mean_cost_per_period_sd"]), 2.)
        pairs = _csv(self.root / "tables/paired.csv")
        average = next(x for x in pairs if x["aggregate"] == "mean_of_available_repeats")
        self.assertEqual(int(average["n_paths"]), 3)  # Not 3 generated repeats × 3 paths.
        self.assertEqual(int(average["n_repeats"]), 3)
        self.assertAlmostEqual(float(average["improvement_pct"]), 100 * 8 / 30)
        self.assertEqual(json.loads(average["cost_difference_ci"]), [-8., -8.])

    def test_all_windows_are_required_for_one_completed_primary(self):
        windows = tuple((mode, h) for mode in ("steady", "cold_start") for h in (50, 100, 200, 500))
        _evaluation(self.root, "self_evolve_h200_r1", [1, 2, 3], windows=windows)
        result = self.run_report()
        self.assertEqual(result["primary_fully_evaluated"], 1)
        self.assertEqual(result["primary_provenance_complete"], 1)
        self.assertFalse(result["complete"])

    def test_metric_mismatch_and_duplicate_are_rejected_not_selected(self):
        path = _evaluation(self.root, "self_evolve_h200_r1", [1, 2, 3])
        rows = json.loads(path.read_text())
        rows[0]["mean_cost_per_period"] = 1
        _save(path, rows)
        result = self.run_report()
        self.assertEqual(result["primary_h200_available"], 0)
        self.assertIn("metric mismatch", result["issues"][0]["error"])
        path = _evaluation(self.root, "self_evolve_h200_r1", [1, 2, 3])
        rows = json.loads(path.read_text()); _save(path, rows + rows)
        result = self.run_report()
        self.assertEqual(result["primary_h200_available"], 0)
        self.assertIn("Duplicate", result["issues"][0]["error"])

    def test_mismatched_path_order_blocks_pairing(self):
        _evaluation(self.root, "baseline_h200_constant_order", [20, 30, 40], family="constant_order", repeat=None)
        _evaluation(self.root, "self_evolve_h200_r1", [10, 20, 30], demand=[3000.3, 2000.2, 1000.1])
        result = self.run_report()
        self.assertEqual(result["paired_rows"], 0)
        self.assertTrue(any("Paired path" in x["error"] for x in result["issues"]))

    def test_training_reference_uses_train_even_when_test_ranking_reverses(self):
        from .analysis_report import BASELINES
        records = {name: {"training": {"mean_cost_per_period": index + 1}} for index, name in enumerate(BASELINES)}
        _save(self.root / "baselines" / SID / "h200" / "records.json", records)
        _evaluation(self.root, "baseline_h200_constant_order", [100, 100, 100], family="constant_order", repeat=None)
        _evaluation(self.root, "baseline_h200_base_stock", [1, 1, 1], family="base_stock", repeat=None)
        result = self.run_report()
        self.assertEqual(result["selected_training_references"][0]["reference_family"], "constant_order")
        self.assertTrue(result["selected_training_references"][0]["selection_complete"])

    def test_source_change_between_windows_is_rejected(self):
        path = _evaluation(self.root, "self_evolve_h200_r1", [1, 2, 3], windows=(("steady", 200), ("steady", 500)))
        rows = json.loads(path.read_text()); rows[1]["code_sha256"] = "f" * 64; _save(path, rows)
        records, issues = load_evaluations(self.root)
        self.assertEqual(records, [])
        self.assertIn("source hash changed", issues[0]["error"])

    def test_incremental_update_preserves_completed_comparison_cache(self):
        _evaluation(self.root, "baseline_h200_constant_order", [20, 30, 40], family="constant_order", repeat=None)
        _evaluation(self.root, "self_evolve_h200_r1", [10, 20, 30])
        self.run_report()
        cache = {p.name: p.stat().st_mtime_ns for p in (self.root / "analysis_cache").glob("*.json")}
        _evaluation(self.root, "self_evolve_h200_r2", [12, 22, 32], repeat=2)
        result = self.run_report()
        self.assertEqual(result["primary_h200_available"], 2)
        for name, timestamp in cache.items():
            self.assertEqual((self.root / "analysis_cache" / name).stat().st_mtime_ns, timestamp)


if __name__ == "__main__":
    unittest.main()
