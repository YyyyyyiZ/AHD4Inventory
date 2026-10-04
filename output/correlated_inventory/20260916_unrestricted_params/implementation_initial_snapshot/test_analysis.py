"""Tiny offline report fixtures; no generated policy or real test tape is run."""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from .analysis_report import report, load_evaluations, generation_quality


SID = "exp_iid_fixed6"


def _save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj))


def _manifest(root):
    _save(root / "dataset_manifest.json", {"files": [{"scenario_id": sid, "split": "test", "n_paths": 3, "arrays_sha256": "a" * 64}
                                                     for sid in (SID, "exp_ar_pos08_fixed6")]})


def _evaluation(root, policy_id, costs, *, family="self_evolve", repeat=1, full=True,
                windows=(("steady", 200),), training_horizon=200, demand=None, scenario_id=SID):
    arrays, rows = {}, []
    directory = root / "evaluation" / scenario_id / policy_id
    directory.mkdir(parents=True, exist_ok=True)
    demand = np.array([1000.1, 2000.2, 3000.3]) if demand is None else np.array(demand)
    for mode, horizon in windows:
        prefix = f"{mode}_h{horizon}"
        values = {"total_cost": np.array(costs) * horizon, "holding_cost": np.array(costs) * horizon,
                  "lost_units": np.zeros(3), "demand_units": demand, "sales_units": demand, "order_units": np.full(3, 50 * horizon)}
        arrays.update({prefix + "_" + name: value for name, value in values.items()})
        rows.append(dict(scenario_id=scenario_id, policy_id=policy_id, family=family, repeat=repeat, full_protocol=full,
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


def _candidate(root, category, horizon=200, index=0, objective=1., code="def f(): return 1", population=10, generations=10):
    sid = SID if horizon == 200 else "exp_ar_pos08_fixed6"
    directory = root / category / sid / f"self_evolve_h{horizon}_r1"
    _save(directory / "search_definition.json", dict(scenario={"scenario_id": sid}, horizon=horizon, repeat=1,
                                                     population_size=population, generations=generations))
    path = directory / "candidates" / f"g001_m2_{index:03d}.json.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt") as handle:
        json.dump(dict(context=dict(generation=1, operator="m2", candidate_index=index),
                       offspring=dict(code=code, objective=objective), model_requests=2,
                       code_sha256=hashlib.sha256(code.encode()).hexdigest() if code else None), handle)
    return directory, path


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

    def test_horizon_refit_diagonal_uses_matched_training_baselines(self):
        sid = "exp_ar_pos08_fixed6"
        windows = (("steady", 50), ("cold_start", 50), ("steady", 200))
        _evaluation(self.root, "baseline_h50_constant_order", [20, 30, 40], family="constant_order", repeat=None,
                    windows=windows, training_horizon=50, scenario_id=sid)
        # A strong H=200 rule evaluated at H=50 must not become the H=50-refit reference.
        _evaluation(self.root, "baseline_h200_constant_order", [1, 1, 1], family="constant_order", repeat=None,
                    windows=(("steady", 50), ("cold_start", 50)), scenario_id=sid)
        for rep in (1, 2, 3):
            _evaluation(self.root, f"self_evolve_h50_r{rep}", [8+2*rep, 18+2*rep, 28+2*rep], repeat=rep,
                        windows=windows, training_horizon=50, scenario_id=sid)
        result = self.run_report()
        self.assertEqual(result["primary_h200_available"], 0)
        self.assertEqual(result["horizon_refit"]["self_evolve_groups_with_both_diagonals"], 3)
        self.assertEqual(result["horizon_refit"]["raw_diagonal_rows"], 8)
        table = _csv(self.root / "tables/horizon_refit.csv")
        self.assertEqual(len(table), 64)
        own = next(r for r in table if r["family"] == "self_evolve" and r["mode"] == "steady" and r["evaluation_horizon"] == "50")
        self.assertEqual(float(own["mean_cost_per_period_mean"]), 22)
        self.assertEqual(float(own["mean_cost_per_period_sd"]), 2)
        pairs = _csv(self.root / "tables/horizon_refit_paired.csv")
        self.assertEqual(len(pairs), 8)
        self.assertTrue(all(r["source_training_horizon"] == r["reference_training_horizon"] == r["horizon"] == "50" for r in pairs))
        self.assertTrue(all(float(r["reference_mean_cost"]) == 30 for r in pairs))

    def test_horizon_refit_excludes_pilot_even_with_expected_policy_id(self):
        _evaluation(self.root, "self_evolve_h50_r1", [1, 2, 3], full=False, training_horizon=50,
                    windows=(("steady", 50), ("cold_start", 50)), scenario_id="exp_ar_pos08_fixed6")
        result = self.run_report()
        self.assertEqual(result["horizon_refit"]["raw_diagonal_rows"], 0)
        self.assertEqual(result["horizon_refit"]["self_evolve_groups_with_both_diagonals"], 0)

    def test_candidate_quality_fixed_denominators_separate_pilot_and_extension(self):
        _candidate(self.root, "training")
        _candidate(self.root, "training", index=1, objective=None, code=None)
        _candidate(self.root, "training", index=2, objective=float("inf"))
        _candidate(self.root, "training", horizon=50)
        pilot, _ = _candidate(self.root, "pilots", population=1, generations=1)
        _save(pilot / "completed.json", {"status": "completed"})
        result = self.run_report()
        quality = json.loads((self.root / "generation_quality.json").read_text())
        main = quality["scopes"]["primary"]
        self.assertEqual(main["planned_chains"], 18)
        self.assertEqual(main["planned_candidate_slots"], 1800)
        self.assertEqual(main["recorded_candidate_slots"], 3)
        self.assertEqual(main["valid_candidate_slots"], 1)
        self.assertEqual(main["invalid_candidate_slots"], 2)
        self.assertAlmostEqual(main["valid_rate_classified_slots"], 1/3)
        self.assertEqual(main["model_requests_recorded_slots"], 6)
        self.assertEqual(main["not_yet_recorded_slots"], 1797)
        self.assertFalse(main["denominator_complete"])
        self.assertEqual(quality["scopes"]["horizon_extension"]["planned_candidate_slots"], 900)
        self.assertEqual(quality["scopes"]["horizon_extension"]["valid_candidate_slots"], 1)
        self.assertTrue(quality["scopes"]["pilot"]["denominator_complete"])
        self.assertEqual(result["primary_h200_available"], 0)
        text = (self.root / "report.md").read_text()
        self.assertIn("白名单", text)
        self.assertIn("有效率", text)

    def test_candidate_corruption_is_unclassified_not_model_failure(self):
        directory, path = _candidate(self.root, "training")
        with gzip.open(path, "rt") as handle:
            saved = json.load(handle)
        saved["code_sha256"] = "wrong"
        with gzip.open(path, "wt") as handle:
            json.dump(saved, handle)
        (directory / "candidates" / "g001_m2_001.json.gz").write_bytes(b"incomplete")
        main = generation_quality(self.root)["scopes"]["primary"]
        self.assertEqual(main["invalid_candidate_slots"], 0)
        self.assertEqual(main["unclassified_candidate_slots"], 2)
        self.assertIsNone(main["valid_rate_classified_slots"])

    def test_transport_failure_is_invalid_subset_and_charge_is_held_once(self):
        directory, path = _candidate(self.root, "training", code=None, objective=None)
        _candidate(self.root, "training", index=1, code=None, objective=None)
        _candidate(self.root, "training", index=2)
        with gzip.open(path, "rt") as handle:
            candidate = json.load(handle)
        candidate["model_requests"] = 1
        candidate["transport_failure"] = dict(request_id="failed-request", error_type="IncompleteRead",
                                              resolution="retain_upper_bound_skip_candidate",
                                              unknown_cost_upper_usd=.0087542, no_response_available=True,
                                              no_repost=True, no_replacement_candidate=True)
        with gzip.open(path, "wt") as handle:
            json.dump(candidate, handle)
        _save(self.root / "request_reconciliations/failed-request.json", candidate["transport_failure"])
        _save(self.root / "api_budget.json", {"limit_usd": 20, "requests": {
            "failed-request": dict(state="unknown_charge", reserved_usd=.0087542, actual_cost_usd=None,
                                    metadata={"chain_dir": str(directory)}),
            "completed-request": dict(state="complete", reserved_usd=.5, actual_cost_usd=.01,
                                       metadata={"chain_dir": str(directory)})}})
        ledger_before, candidate_before = (self.root / "api_budget.json").read_bytes(), path.read_bytes()
        self.run_report()
        quality = json.loads((self.root / "generation_quality.json").read_text())
        main, account = quality["scopes"]["primary"], quality["accounting"]
        self.assertEqual(main["recorded_candidate_slots"], 3)
        self.assertEqual(main["valid_candidate_slots"], 1)
        self.assertEqual(main["invalid_candidate_slots"], 2)  # Existing total is unchanged.
        self.assertEqual(main["transport_failure_slots"], 1)
        self.assertEqual(main["model_or_constraint_invalid_slots"], 1)
        self.assertAlmostEqual(main["valid_rate_classified_slots"], 1/3)
        self.assertEqual(main["model_requests_recorded_slots"], 5)
        self.assertEqual(quality["transport_failure_records"][0]["request_id"], "failed-request")
        self.assertAlmostEqual(account["known_cost_usd"], .01)
        self.assertAlmostEqual(account["uncertain_held_upper_usd"], .0087542)
        self.assertAlmostEqual(account["committed_upper_usd"], .0187542)
        self.assertEqual(account["uncertain_requests"], 1)
        self.assertEqual(account["pending_requests"], 0)
        self.assertEqual(account["requests"], 2)
        self.assertEqual((self.root / "api_budget.json").read_bytes(), ledger_before)
        self.assertEqual(path.read_bytes(), candidate_before)
        text = (self.root / "report.md").read_text()
        self.assertIn("输出/约束无效 | 通信失败", text)
        self.assertIn("无效合计包括通信失败", text)
        chain = next(row for row in _csv(self.root / "tables/generation_quality.csv") if row["chain"] == str(directory.relative_to(self.root)))
        self.assertEqual(chain["transport_failure_slots"], "1")

    def test_transport_label_without_evidence_is_not_a_model_failure(self):
        _, path = _candidate(self.root, "training", code=None, objective=None)
        with gzip.open(path, "rt") as handle:
            candidate = json.load(handle)
        candidate["transport_failure"] = {}
        with gzip.open(path, "wt") as handle:
            json.dump(candidate, handle)
        quality = generation_quality(self.root)
        main = quality["scopes"]["primary"]
        self.assertEqual(main["transport_failure_slots"], 0)
        self.assertEqual(main["invalid_candidate_slots"], 0)
        self.assertEqual(main["unclassified_candidate_slots"], 1)
        self.assertIn("request identity", quality["issues"][0]["error"])

    def test_budget_snapshot_includes_preflight_pilot_unknown_and_pending(self):
        main, _ = _candidate(self.root, "training")
        pilot, _ = _candidate(self.root, "pilots", population=1, generations=1)
        entries = {
            "preflight": dict(state="complete", actual_cost_usd=.01, reserved_usd=.5, metadata={"phase": "preflight"}),
            "pilot": dict(state="complete", actual_cost_usd=.02, reserved_usd=.5, metadata={"chain_dir": str(pilot)}),
            "known": dict(state="complete", actual_cost_usd=.03, reserved_usd=.5, metadata={"chain_dir": str(main)}),
            "unknown": dict(state="unknown_charge", actual_cost_usd=None, reserved_usd=.1, metadata={"chain_dir": str(main)}),
            "missing": dict(state="missing_cost", actual_cost_usd=None, reserved_usd=.2, metadata={"chain_dir": str(main)}),
            "pending": dict(state="pending", reserved_usd=.3, metadata={"chain_dir": str(main)}),
        }
        _save(self.root / "api_budget.json", {"limit_usd": 20, "requests": entries})
        before = (self.root / "api_budget.json").read_bytes()
        account = generation_quality(self.root)["accounting"]
        self.assertAlmostEqual(account["known_cost_usd"], .06)
        self.assertAlmostEqual(account["uncertain_held_upper_usd"], .3)
        self.assertAlmostEqual(account["pending_upper_usd"], .3)
        self.assertAlmostEqual(account["held_upper_usd"], .6)
        self.assertAlmostEqual(account["committed_upper_usd"], .66)
        self.assertEqual(account["requests"], 6)
        self.assertEqual(account["uncertain_requests"], 2)
        self.assertEqual(account["pending_requests"], 1)
        self.assertEqual(account["categories"]["pilot"]["known_cost_usd"], .02)
        self.assertEqual(account["categories"]["preflight"]["known_cost_usd"], .01)
        self.assertEqual((self.root / "api_budget.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
