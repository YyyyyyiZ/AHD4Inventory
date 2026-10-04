"""Offline synthetic checks for cross-run, whole-path parameter-cap ablation."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from .analysis_report import BASELINES, HORIZONS
from .compare_parameter_runs import compare_runs, count_opt_params, parameter_inventory, _sha
from .data import scenario_specs
from .test_analysis import _evaluation, _save


SID = "exp_iid_fixed6"
SIGNATURE = "def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):\n"


def code_with_parameters(count):
    return SIGNATURE + "".join(f"    p{i} = {i+1}.0  # OPT_PARAM: {{'initial': {i+1}.0}}\n" for i in range(count)) + "    return 0.0\n"


class ParameterComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old, self.new, self.output = (self.root / name for name in ("old", "new", "comparison"))
        self.manifest = {"files": [dict(scenario_id=spec.scenario_id, split=split, arrays_sha256="a"*64,
                                        n_paths=3, n_periods=1000)
                                  for spec in scenario_specs() for split in ("train", "validation", "test")]}
        for root in (self.old, self.new):
            _save(root / "dataset_manifest.json", self.manifest)

    def tearDown(self):
        self.temp.cleanup()

    def add_design(self, root, sid=SID, training_horizon=200, *, repeats=(1, 2, 3), all_windows=False):
        windows = tuple((mode, h) for mode in ("steady", "cold_start") for h in HORIZONS) if all_windows else (("steady", 200),)
        records = {family: dict(name=family, theta=[1.0], fixture=True) for family in BASELINES}
        _save(root / "baselines" / sid / f"h{training_horizon}" / "records.json", records)
        for family, costs in (("conditional_pil", [25, 35, 45]), ("forecast_adaptive_pil", [22, 32, 42])):
            path = _evaluation(root, f"baseline_h{training_horizon}_{family}", costs, family=family, repeat=None,
                               scenario_id=sid, windows=windows, training_horizon=training_horizon)
            rows = json.loads(path.read_text())
            for row in rows:
                row.update(record_sha256=_sha(records[family]), code_sha256=None)
            _save(path, rows)
        for repeat in repeats:
            # Means old=22, new=12; each pair differs by exactly -10 on each path.
            offset = 10 if root == self.old else 0
            _evaluation(root, f"self_evolve_h{training_horizon}_r{repeat}",
                        [offset+2*repeat-2, offset+2*repeat+8, offset+2*repeat+18],
                        repeat=repeat, scenario_id=sid, windows=windows, training_horizon=training_horizon)

    def compare(self):
        return compare_runs(self.old, self.new, self.output, n_bootstrap=40)

    def test_three_repeat_path_mean_and_ci_direction(self):
        self.add_design(self.old); self.add_design(self.new)
        result = self.compare()
        row = next(row for row in result["main"] if row["scenario_id"] == SID)
        self.assertEqual(row["status"], "complete")
        self.assertEqual(row["old_mean_cost_per_period"], 22.0)
        self.assertEqual(row["new_mean_cost_per_period"], 12.0)
        self.assertEqual(row["old_generation_sd"], 2.0)
        comparison = next(row for row in result["comparisons"] if row["comparison"] == "new_vs_old")
        self.assertEqual(comparison["n_paths"], 3)  # Never 3 repeats × 3 paths.
        self.assertEqual(comparison["cost_difference_ci"], [-10., -10.])
        self.assertEqual(comparison["significant_outcome"], "win")
        self.assertAlmostEqual(comparison["improvement_pct"], 1000/22)
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("旧轮测试结果已经查看", (self.output / "report.md").read_text())

    def test_partial_repeats_are_not_a_three_repeat_result(self):
        self.add_design(self.old); self.add_design(self.new, repeats=(1, 2))
        result = self.compare()
        row = next(row for row in result["main"] if row["scenario_id"] == SID)
        self.assertEqual(row["new_n_repeats"], 2)
        self.assertNotIn("new_mean_cost_per_period", row)
        self.assertEqual(result["comparisons"], [])

    def test_mismatched_manifest_blocks_pairing(self):
        self.add_design(self.old); self.add_design(self.new)
        manifest = json.loads((self.new / "dataset_manifest.json").read_text())
        for entry in manifest["files"]:
            if entry["scenario_id"] == SID and entry["split"] == "test":
                entry["arrays_sha256"] = "b"*64
        _save(self.new / "dataset_manifest.json", manifest)
        result = self.compare()
        self.assertEqual(result["comparisons"], [])
        self.assertTrue(any(row["status"] == "mismatch" for row in result["dataset_pairing"]))

    def test_changed_baseline_record_blocks_common_reference(self):
        self.add_design(self.old); self.add_design(self.new)
        path = self.new / "baselines" / SID / "h200" / "records.json"
        rows = json.loads(path.read_text()); rows["conditional_pil"]["theta"] = [2.0]; _save(path, rows)
        result = self.compare()
        self.assertEqual(result["comparisons"], [])
        self.assertTrue(any("Baseline source" in row["error"] for row in result["issues"]))

    def test_parameter_declarations_are_not_four_inputs_or_string_mentions(self):
        self.assertEqual(count_opt_params(SIGNATURE+'    """OPT_PARAM: is a comment marker."""\n    return 0.0\n'), 0)
        self.assertEqual(count_opt_params(code_with_parameters(7)), 7)
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            count_opt_params(SIGNATURE+"    a=1; b=2 # OPT_PARAM: {}\n    return a+b\n")
        chain = self.new / "training" / SID / "self_evolve_h200_r1"
        metadata = dict(generation=1, operator="m2", candidate_index=0, candidate_attempt=1)
        _save(chain / "model_responses" / "one.json", dict(state="complete", metadata=metadata,
              content="```python\n"+code_with_parameters(7)+"```"))
        _save(chain / "model_responses" / "two.json", dict(state="pending", metadata={**metadata,"candidate_attempt":2}))
        code = code_with_parameters(6); chain.mkdir(parents=True, exist_ok=True); (chain / "policy.py").write_text(code)
        _save(chain / "completed.json", dict(status="completed", best_code_path="policy.py",
                                             code_sha256=hashlib.sha256(code.encode()).hexdigest()))
        rows, summaries, _, issues = parameter_inventory(self.new, "new")
        self.assertEqual(issues, [])
        self.assertEqual([row["opt_param_count"] for row in rows], [7, None, 6])
        generated = next(row for row in summaries if row["scope"] == "primary" and row["stage"] == "generated_response")
        self.assertEqual((generated["counted"], generated["pending"], generated["above_four"]), (1,1,1))

    def test_complete_grid_and_final_sources_can_reach_complete(self):
        designs = [(spec.scenario_id, 200) for spec in scenario_specs()]
        designs += [("exp_ar_pos08_fixed6", h) for h in (50,100,500)]
        for root in (self.old,self.new):
            for sid, h in designs:
                self.add_design(root, sid, h, all_windows=True)
                for repeat in (1,2,3):
                    chain = root / "training" / sid / f"self_evolve_h{h}_r{repeat}"
                    chain.mkdir(parents=True, exist_ok=True)
                    code = code_with_parameters(4 if root == self.old else 6)
                    (chain / "policy.py").write_text(code)
                    _save(chain / "completed.json", dict(status="completed", best_code_path="policy.py",
                        code_sha256=hashlib.sha256(code.encode()).hexdigest()))
        result = self.compare()
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["complete_comparison_windows"], 72)
        self.assertEqual(len(result["comparisons"]), 360)

    def test_root_cli_and_require_complete_exit(self):
        answer = subprocess.run([sys.executable, "-B", "-m", "examples.inventory.correlated_benchmark.compare_parameter_runs",
            "--previous-run", str(self.old), "--run-dir", str(self.new), "--require-complete", "--bootstrap", "5"],
            capture_output=True, text=True)
        self.assertEqual(answer.returncode, 2, answer.stderr)
        self.assertEqual(json.loads(answer.stdout)["status"], "incomplete")
        self.assertTrue((self.new / "parameter_comparison" / "report.md").exists())


if __name__ == "__main__":
    unittest.main()
