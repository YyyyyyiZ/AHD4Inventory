"""Network-free report fixtures; never generate or execute inventory policies."""
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from .adaptive_pil_report import PIL_FAMILIES, budget_accounting, report, training_progress
from .data import scenario_specs


WINDOWS = tuple((mode, h) for mode in ("steady", "cold_start") for h in (50, 100, 200, 500))
SID = "exp_iid_fixed6"


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def fixture_root(root):
    save(root / "dataset_manifest.json", {"files": [dict(scenario_id=s.scenario_id, split="test", n_paths=3,
                                                        arrays_sha256="a"*64) for s in scenario_specs()]})


def baseline_records(root, sid=SID, cost=30.):
    records = {name: dict(name=name, scenario={"scenario_id": sid},
                         training=dict(n_paths=50, burnin=500, horizon=200, mean_cost_per_period=cost))
               for name in PIL_FAMILIES}
    save(root / "baselines" / sid / "h200/records.json", records)
    return records


def evaluation(root, costs, *, sid=SID, repeat=1, family="self_evolve", windows=WINDOWS, demand=None):
    if family == "self_evolve":
        pid = f"self_evolve_h200_r{repeat}"
        source = root / "training" / sid / pid
        source.mkdir(parents=True, exist_ok=True)
        code = f"def compute_order_amount(i,p,d,l): return {repeat}\n"
        (source / "policy.py").write_text(code)
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        record_hash = None
        save(source / "completed.json", dict(status="completed", full_protocol=True, scenario_id=sid,
             policy_id=pid, repeat=repeat, source_training_horizon=200, code_sha256=code_hash,
             best_train_cost=float(np.mean(costs))*200))
    else:
        pid = "baseline_h200_" + family
        records = json.loads((root / "baselines" / sid / "h200/records.json").read_text())
        record_hash = hashlib.sha256(json.dumps(records[family], sort_keys=True).encode()).hexdigest()
        code_hash, repeat = None, None
    directory = root / "evaluation" / sid / pid
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "test.npz"
    demand = np.array([1000.1, 2000.2, 3000.3]) if demand is None else np.array(demand)
    arrays, rows = {}, []
    for mode, h in windows:
        prefix = f"{mode}_h{h}"
        arrays.update({prefix+"_"+key: value for key, value in
                      dict(total_cost=np.array(costs)*h, holding_cost=np.array(costs)*h,
                           lost_units=np.zeros(3), demand_units=demand, sales_units=demand,
                           order_units=np.full(3, 50*h)).items()})
        rows.append(dict(scenario_id=sid, policy_id=pid, family=family, repeat=repeat, split="test",
                         mode=mode, horizon=h, source_training_horizon=200, full_protocol=True,
                         costs_path=str(path.relative_to(root)), array_prefix=prefix,
                         mean_cost_per_period=float(np.mean(costs)), holding_per_period=float(np.mean(costs)),
                         lost_units_per_period=0., fill_rate=1., orders_per_period=50.,
                         dataset_arrays_sha256="a"*64, code_sha256=code_hash, record_sha256=record_hash))
    np.savez_compressed(path, **arrays)
    for row in rows:
        row["costs_file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    save(directory / "test.json", rows)


class AdaptivePILReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "new"
        self.capped = Path(self.temp.name) / "capped"
        self.unrestricted = Path(self.temp.name) / "unrestricted"
        for root in (self.root, self.capped, self.unrestricted):
            fixture_root(root)

    def tearDown(self):
        self.temp.cleanup()

    def run_report(self):
        return report(self.root, self.capped, self.unrestricted, n_bootstrap=40, make_plots=False)

    def test_empty_reports_pending_eighteen_not_complete(self):
        result = self.run_report()
        self.assertEqual(result["status"], "pending_primary")
        self.assertEqual(result["expected_primary_runs"], 18)
        self.assertEqual(result["completed_primary_runs"], 0)
        self.assertEqual(len(result["comparisons"]), 240)
        self.assertTrue(result["old_comparison_pending"])
        self.assertTrue(all(row["new_mean_cost_per_period"] is None for row in result["windows"]))

    def test_complete_repeat_mean_sd_pairing_and_pending_old_average(self):
        baseline_records(self.root)
        for family in PIL_FAMILIES:
            evaluation(self.root, [20, 30, 40], family=family)
        for repeat in (1, 2, 3):
            evaluation(self.root, [8+2*repeat, 18+2*repeat, 28+2*repeat], repeat=repeat)
            evaluation(self.capped, [30, 40, 50], repeat=repeat)
        for repeat in (1, 2):
            evaluation(self.unrestricted, [1, 2, 3], repeat=repeat)
        result = self.run_report()
        row = next(r for r in result["windows"] if (r["scenario_id"], r["mode"], r["horizon"]) == (SID, "steady", 200))
        self.assertEqual(row["new_mean_cost_per_period"], 22)
        self.assertEqual(row["new_generation_sd"], 2)
        self.assertIsNone(row["unrestricted_evolve_mean_cost_per_period"])
        pair = next(r for r in result["comparisons"] if (r["scenario_id"], r["mode"], r["horizon"], r["reference"]) == (SID, "steady", 200, "forecast_adaptive_pil"))
        self.assertEqual(pair["n_paths"], 3)  # Not nine generated-repeat × path observations.
        self.assertEqual(pair["candidate_repeats"], 3)
        self.assertEqual(pair["reference_repeats"], 1)
        self.assertEqual(pair["mean_cost_difference"], -8)
        self.assertEqual(pair["cost_difference_ci"], [-8., -8.])
        self.assertAlmostEqual(pair["improvement_pct"], 100*8/30)
        self.assertTrue(row["primary_ready"])
        self.assertEqual(row["unrestricted_evolve_status"], "pending")

    def test_two_new_repeats_have_no_new_mean_or_bootstrap(self):
        baseline_records(self.root)
        evaluation(self.root, [20, 30, 40], family="forecast_adaptive_pil")
        for repeat in (1, 2):
            evaluation(self.root, [1, 2, 3], repeat=repeat)
        result = self.run_report()
        rows = [r for r in result["windows"] if r["scenario_id"] == SID]
        self.assertTrue(all(r["new_n_repeats"] == 2 for r in rows))
        self.assertTrue(all(r["new_mean_cost_per_period"] is None for r in rows))
        self.assertEqual(result["completed_comparisons"], 0)

    def test_new_primary_complete_without_old_results(self):
        for spec in scenario_specs():
            baseline_records(self.root, spec.scenario_id)
            for family in PIL_FAMILIES:
                evaluation(self.root, [20, 30, 40], sid=spec.scenario_id, family=family)
            for repeat in (1, 2, 3):
                evaluation(self.root, [10, 20, 30], sid=spec.scenario_id, repeat=repeat)
        result = self.run_report()
        self.assertTrue(result["completed_primary"])
        self.assertFalse(result["completed_all_comparisons"])
        self.assertEqual(result["status"], "completed_primary")
        self.assertEqual(result["completed_primary_runs"], 18)
        self.assertEqual(result["primary_ready_windows"], 48)
        self.assertEqual(result["completed_comparisons"], 144)
        self.assertTrue(result["old_comparison_pending"])
        for root in (self.capped, self.unrestricted):
            for spec in scenario_specs():
                for repeat in (1, 2, 3):
                    evaluation(root, [20, 30, 40], sid=spec.scenario_id, repeat=repeat)
        result = self.run_report()
        self.assertTrue(result["completed_all_comparisons"])
        self.assertEqual(result["status"], "completed_all_comparisons")
        self.assertEqual(result["completed_comparisons"], 240)
        self.assertFalse(result["old_comparison_pending"])

    def test_path_reordering_blocks_comparison(self):
        baseline_records(self.root)
        evaluation(self.root, [20, 30, 40], family="forecast_adaptive_pil", demand=[3000.3, 2000.2, 1000.1])
        for repeat in (1, 2, 3):
            evaluation(self.root, [10, 20, 30], repeat=repeat)
        result = self.run_report()
        self.assertEqual(result["completed_comparisons"], 0)
        self.assertTrue(any("ordered demand paths" in issue["error"] for issue in result["issues"]))

    def test_training_original_seed_gen0_and_final_keep_correct_units(self):
        baseline_records(self.root, cost=100.)
        directory = self.root / "training" / SID / "self_evolve_h200_r1"
        save(directory / "pops/population_generation_0.json", [{"objective": 18000}])
        save(directory / "completed.json", {"status": "completed", "best_train_cost": 14000})
        path = directory / "checkpoints/g001.json.gz"
        path.parent.mkdir(parents=True)
        with gzip.open(path, "wt") as handle:
            json.dump({"generation": 1, "best_train_cost": 17000}, handle)
        curves, improvements, issues = training_progress(self.root)
        self.assertEqual(issues, [])
        row = next(r for r in improvements if r["scenario_id"] == SID and r["repeat"] == 1)
        self.assertEqual(row["original_adaptive_train_cost_per_period"], 100)
        self.assertEqual(row["optimized_gen0_train_cost_per_period"], 90)
        self.assertEqual(row["final_train_cost_per_period"], 70)
        self.assertEqual(row["seed_to_final_improvement_pct"], 30)
        self.assertEqual(row["gen0_to_final_cost_reduction"], 20)
        curve = {r["generation"]: r["mean_train_cost_per_period"] for r in curves if r["scenario_id"] == SID and r["repeat"] == 1}
        self.assertEqual(curve, {-1: 100, 0: 90, 1: 85})

    def test_shared_ledger_attribution_and_previous_commitment_added_once(self):
        save(self.root / "protocol.json", {"configuration": {"shared_budget_run_dir": str(self.unrestricted),
             "previous_committed_upper_usd": 1.82576175, "session_budget_usd": 20}})
        new_chain = self.root / "training" / SID / "self_evolve_h200_r1"
        entries = {
            "new": dict(state="complete", actual_cost_usd=.1, reserved_usd=.5, metadata={"chain_dir": str(new_chain)}),
            "other": dict(state="complete", actual_cost_usd=.2, reserved_usd=.5, metadata={"chain_dir": str(self.unrestricted/"training/old")}),
            "preflight": dict(state="complete", actual_cost_usd=.03, reserved_usd=.5, metadata={"phase": "preflight"}),
            "unknown": dict(state="unknown_charge", actual_cost_usd=None, reserved_usd=.04, metadata={"chain_dir": str(new_chain)}),
            "pending": dict(state="pending", reserved_usd=.05, metadata={"chain_dir": str(new_chain)}),
        }
        path = self.unrestricted / "api_budget.json"
        save(path, {"limit_usd": 18.17, "requests": entries})
        before = path.read_bytes()
        account = budget_accounting(self.root.resolve(), self.unrestricted.resolve())
        self.assertAlmostEqual(account["buckets"]["this_run"]["known_cost_usd"], .1)
        self.assertAlmostEqual(account["buckets"]["this_run"]["committed_upper_usd"], .19)
        self.assertAlmostEqual(account["buckets"]["shared_global"]["known_cost_usd"], .33)
        self.assertAlmostEqual(account["buckets"]["shared_global"]["committed_upper_usd"], .42)
        self.assertAlmostEqual(account["session_committed_upper_usd"], 1.82576175+.42)
        self.assertEqual(account["buckets"]["shared_global"]["requests"], 5)
        self.assertEqual(path.read_bytes(), before)

    def test_frozen_policy_source_change_rejected(self):
        evaluation(self.root, [10, 20, 30])
        (self.root / "training" / SID / "self_evolve_h200_r1/policy.py").write_text("changed")
        result = self.run_report()
        self.assertEqual(result["completed_primary_runs"], 0)
        self.assertTrue(any("frozen generated" in r["error"] for r in result["issues"]))


if __name__ == "__main__":
    unittest.main()
