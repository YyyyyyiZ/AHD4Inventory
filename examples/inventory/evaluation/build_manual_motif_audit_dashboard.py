#!/usr/bin/env python3
"""Build a deterministic manual-audit dashboard for motif labels.

The workflow intentionally uses no LLM.  It accelerates human review by:

1. showing the existing motif labels next to deterministic evidence snippets;
2. canonicalizing policies with AST transformations so near-equivalent code can
   be reviewed as a group;
3. producing a static HTML dashboard with filters and a review queue CSV.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import html
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TABLE_MOTIFS = [
    "inventory_position",
    "pipeline_weighting",
    "nonlinear_pipeline_composition",
    "order_up_to",
    "state_dependent_target",
    "partial_adjustment",
    "constant_order",
    "order_clipping",
    "order_smoothing",
]

EXTRA_MOTIFS = [
    "safety_stock_buffer",
    "pipeline_demand_proxy",
    "near_term_pipeline_focus",
    "threshold_order_activation",
    "integer_rounding",
    "emergency_or_shortage_boost",
    "nonlinear_gap_transform",
]

PRESERVE_NAMES = {
    "on_hand_inventory",
    "pipeline_orders",
    "compute_order_amount",
    "sum",
    "max",
    "min",
    "len",
    "int",
    "round",
    "range",
    "enumerate",
    "zip",
    "reversed",
    "sorted",
    "abs",
    "float",
    "ceil",
    "floor",
    "sqrt",
    "log",
    "exp",
}

EVIDENCE_PATTERNS = {
    "inventory_position": [
        r"inventory_position",
        r"on_hand_inventory\s*\+\s*sum\s*\(\s*pipeline_orders\s*\)",
        r"net_inventory|projected_inventory",
    ],
    "pipeline_weighting": [
        r"weight|weighted|discount|effective_pipeline|coverage",
        r"zip\s*\(|enumerate\s*\(",
        r"pipeline_orders\s*\[[^\]]+\]",
    ],
    "nonlinear_pipeline_composition": [
        r"\bmax\s*\(\s*pipeline_orders|\bmin\s*\(\s*pipeline_orders",
        r"std|variance|var|median|percentile",
        r"pipeline.*\*\*|pipeline.*ratio|sum\s*\([^)]*pipeline_orders[^)]*\)\s*/",
    ],
    "order_up_to": [
        r"\bmax\s*\(\s*0\s*,.*-.*inventory",
        r"\bmax\s*\(.*-.*inventory\s*,\s*0\s*\)",
        r"target_.*-.*inventory|base_stock.*-.*inventory|gap",
    ],
    "state_dependent_target": [
        r"target|target_position|target_inventory|adjusted_base|dynamic_base",
        r"expected|forecast|demand|recent|pipeline",
    ],
    "partial_adjustment": [
        r"alpha|beta|gain|smoothing|smooth|adjustment_factor|fraction|partial",
        r"\*\s*(target_order|raw_order|order_amount|gap)|\(.*-.*inventory.*\)\s*\*",
    ],
    "constant_order": [
        r"baseline_order|constant_order|fixed_order",
    ],
    "order_clipping": [
        r"max_order|order_cap|min_order|minimum_order|cap|limit|floor",
        r"\bmin\s*\(|\bmax\s*\(",
    ],
    "order_smoothing": [
        r"previous_order|prev_order|last_order|prior_order",
        r"smooth|smoothing|beta|blend|delta",
    ],
    "safety_stock_buffer": [
        r"safety_stock|safety_buffer|buffer",
    ],
    "pipeline_demand_proxy": [
        r"demand|forecast|estimate|recent",
        r"pipeline_orders",
    ],
    "near_term_pipeline_focus": [
        r"pipeline_orders\s*\[\s*0\s*\]",
        r"pipeline_orders\s*\[\s*:\s*\d+",
        r"recent_|near|arrival",
    ],
    "threshold_order_activation": [
        r"threshold|reorder|critical|min_order|minimum_order",
        r"\bif\b.*(order|gap|inventory|pipeline)",
    ],
    "integer_rounding": [
        r"\bint\s*\(|\bround\s*\(|\bceil\s*\(|\bfloor\s*\(",
    ],
    "emergency_or_shortage_boost": [
        r"emergency|shortage|critical|low_inventory|aggressive|stockout",
    ],
    "nonlinear_gap_transform": [
        r"gap\s*\*\*|raw_order\s*\*\*|order_needed\s*\*\*",
        r"\bsqrt\s*\(|\blog\s*\(|\bexp\s*\(",
    ],
}


@dataclass
class Sample:
    row: dict[str, str]
    code: str
    canonical_code: str
    canonical_hash: str
    evidence: dict[str, list[str]]


class Canonicalizer(ast.NodeTransformer):
    """Normalize policy code for deterministic near-equivalence clustering."""

    def __init__(self) -> None:
        self.name_map: dict[str, str] = {}
        self.next_name = 1

    def canonical_name(self, name: str) -> str:
        if name in PRESERVE_NAMES:
            return name
        if name not in self.name_map:
            self.name_map[name] = f"v{self.next_name}"
            self.next_name += 1
        return self.name_map[name]

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        node.name = "compute_order_amount"
        self.generic_visit(node)
        node.decorator_list = []
        node.returns = None
        return node

    def visit_arg(self, node: ast.arg) -> ast.AST:
        node.arg = self.canonical_name(node.arg)
        node.annotation = None
        return node

    def visit_Name(self, node: ast.Name) -> ast.AST:
        node.id = self.canonical_name(node.id)
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if isinstance(node.value, bool) or node.value is None:
            return node
        if isinstance(node.value, (int, float)):
            return ast.copy_location(ast.Constant(value=1), node)
        if isinstance(node.value, str):
            return ast.copy_location(ast.Constant(value="STR"), node)
        return node


def canonicalize(code: str) -> tuple[str, str]:
    try:
        tree = ast.parse(code)
        tree = Canonicalizer().visit(tree)
        ast.fix_missing_locations(tree)
        canonical = ast.unparse(tree)
    except Exception:
        canonical = re.sub(r"\d+(?:\.\d+)?", "1", code)
        canonical = re.sub(r"#.*", "", canonical)
        canonical = re.sub(r"\s+", " ", canonical).strip()
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return canonical, digest


def line_evidence(code: str, motif: str, max_lines: int = 4) -> list[str]:
    patterns = [re.compile(pattern, re.I) for pattern in EVIDENCE_PATTERNS.get(motif, [])]
    if not patterns:
        return []
    lines = code.splitlines()
    hits: list[str] = []
    for idx, line in enumerate(lines, start=1):
        if any(pattern.search(line) for pattern in patterns):
            hits.append(f"L{idx}: {line.strip()}")
        if len(hits) >= max_lines:
            break
    return hits


def read_samples(sample_dir: Path) -> list[Sample]:
    manifest_path = sample_dir / "sample_100_policy_motif_labels.csv"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")
    samples: list[Sample] = []
    with manifest_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            policy_path = sample_dir / row["policy_file"]
            code = policy_path.read_text(encoding="utf-8")
            # Drop metadata comments from evidence/canonicalization, but keep code comments.
            code_body = "\n".join(line for line in code.splitlines() if not line.startswith("# "))
            canonical_code, canonical_hash = canonicalize(code_body)
            evidence = {
                motif: line_evidence(code_body, motif)
                for motif in TABLE_MOTIFS + EXTRA_MOTIFS
                if row.get(motif) == "True"
            }
            samples.append(Sample(row=row, code=code_body, canonical_code=canonical_code, canonical_hash=canonical_hash, evidence=evidence))
    return samples


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_cluster_rows(samples: list[Sample]) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, int]]:
    groups: dict[str, list[Sample]] = defaultdict(list)
    for sample in samples:
        groups[sample.canonical_hash].append(sample)
    sorted_groups = sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))
    cluster_id_by_hash = {digest: idx for idx, (digest, _) in enumerate(sorted_groups, start=1)}
    cluster_size_by_hash = {digest: len(group) for digest, group in groups.items()}
    rows: list[dict[str, Any]] = []
    for digest, group in sorted_groups:
        motif_counts = {
            motif: sum(sample.row.get(motif) == "True" for sample in group)
            for motif in TABLE_MOTIFS + EXTRA_MOTIFS
        }
        rows.append(
            {
                "cluster_id": cluster_id_by_hash[digest],
                "canonical_hash": digest,
                "cluster_size": len(group),
                "sample_ids": ";".join(sample.row["sample_id"] for sample in group),
                "distributions": ";".join(sorted({sample.row["distribution"] for sample in group})),
                "table_motifs_union": ";".join(motif for motif in TABLE_MOTIFS if motif_counts[motif] > 0),
                "extra_motifs_union": ";".join(motif for motif in EXTRA_MOTIFS if motif_counts[motif] > 0),
                "canonical_excerpt": group[0].canonical_code[:1000].replace("\n", "\\n"),
            }
        )
    return rows, cluster_id_by_hash, cluster_size_by_hash


def build_review_queue(samples: list[Sample], cluster_id_by_hash: dict[str, int], cluster_size_by_hash: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for sample in sorted(samples, key=lambda s: (-cluster_size_by_hash[s.canonical_hash], cluster_id_by_hash[s.canonical_hash], s.row["sample_id"])):
        first_in_cluster = sample.canonical_hash not in seen
        seen.add(sample.canonical_hash)
        rows.append(
            {
                "review_priority": len(rows) + 1,
                "sample_id": sample.row["sample_id"],
                "cluster_id": cluster_id_by_hash[sample.canonical_hash],
                "cluster_size": cluster_size_by_hash[sample.canonical_hash],
                "first_in_cluster": first_in_cluster,
                "policy_file": sample.row["policy_file"],
                "distribution": sample.row["distribution"],
                "generation": sample.row["generation"],
                "rank_in_population_file": sample.row["rank_in_population_file"],
                "table_motifs": sample.row["table_motifs"],
                "extra_motifs": sample.row["extra_motifs"],
                "manual_label_correct": "",
                "manual_notes": "",
            }
        )
    return rows


def motif_badges(row: dict[str, str], motifs: list[str], css_class: str) -> str:
    badges = []
    for motif in motifs:
        if row.get(motif) == "True":
            badges.append(f'<span class="badge {css_class}" data-motif="{motif}">{html.escape(motif)}</span>')
    return "\n".join(badges)


def render_evidence(sample: Sample) -> str:
    parts = []
    for motif in TABLE_MOTIFS + EXTRA_MOTIFS:
        if sample.row.get(motif) != "True":
            continue
        lines = sample.evidence.get(motif) or ["No short regex evidence found; inspect code."]
        rendered = "".join(f"<li>{html.escape(line)}</li>" for line in lines)
        parts.append(f"<div class='evidence-block'><b>{html.escape(motif)}</b><ul>{rendered}</ul></div>")
    return "\n".join(parts)


def build_html(samples: list[Sample], cluster_id_by_hash: dict[str, int], cluster_size_by_hash: dict[str, int]) -> str:
    motif_options = "\n".join(
        f'<option value="{html.escape(motif)}">{html.escape(motif)}</option>'
        for motif in TABLE_MOTIFS + EXTRA_MOTIFS
    )
    cards = []
    for sample in samples:
        row = sample.row
        true_motifs = [motif for motif in TABLE_MOTIFS + EXTRA_MOTIFS if row.get(motif) == "True"]
        data = {
            "sample": row["sample_id"],
            "cluster": cluster_id_by_hash[sample.canonical_hash],
            "clusterSize": cluster_size_by_hash[sample.canonical_hash],
            "distribution": row["distribution"],
            "top10": row.get("is_top10_by_distribution", "False"),
            "final": row.get("is_final_generation", "False"),
            "motifs": true_motifs,
        }
        cards.append(
            f"""
<section class="card" data-record='{html.escape(json.dumps(data, sort_keys=True))}'>
  <div class="card-head">
    <div>
      <h2>Sample {html.escape(row["sample_id"])} · Cluster {cluster_id_by_hash[sample.canonical_hash]} ({cluster_size_by_hash[sample.canonical_hash]})</h2>
      <p>{html.escape(row["distribution"])} · gen {html.escape(row["generation"])} · rank {html.escape(row["rank_in_population_file"])} · objective {html.escape(row["objective"])}</p>
    </div>
    <div class="flags">
      <span class="flag">top10: {html.escape(row.get("is_top10_by_distribution", ""))}</span>
      <span class="flag">final: {html.escape(row.get("is_final_generation", ""))}</span>
    </div>
  </div>
  <div class="badges">
    {motif_badges(row, TABLE_MOTIFS, "table")}
    {motif_badges(row, EXTRA_MOTIFS, "extra")}
  </div>
  <div class="cols">
    <div>
      <h3>Evidence Lines</h3>
      {render_evidence(sample)}
    </div>
    <div>
      <h3>Canonical Structure</h3>
      <pre>{html.escape(sample.canonical_code[:2500])}</pre>
    </div>
  </div>
  <details>
    <summary>Original policy code</summary>
    <pre>{html.escape(sample.code)}</pre>
  </details>
</section>
"""
        )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Manual Motif Audit Dashboard</title>
<style>
body {{ margin: 0; font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #1f2933; background: #f7f8fa; }}
header {{ position: sticky; top: 0; z-index: 10; padding: 16px 20px; background: #ffffff; border-bottom: 1px solid #d9dee7; }}
h1 {{ margin: 0 0 10px; font-size: 22px; }}
.controls {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }}
select, input, button {{ font: inherit; padding: 7px 9px; border: 1px solid #c8d0dc; border-radius: 6px; background: white; }}
button {{ cursor: pointer; }}
main {{ padding: 16px 20px 36px; }}
.summary {{ margin-bottom: 12px; color: #52606d; }}
.card {{ background: white; border: 1px solid #d9dee7; border-radius: 8px; margin: 12px 0; padding: 14px; }}
.card-head {{ display: flex; justify-content: space-between; gap: 12px; }}
h2 {{ margin: 0; font-size: 17px; }}
h3 {{ margin: 12px 0 6px; font-size: 14px; }}
p {{ margin: 4px 0; color: #52606d; }}
.badges {{ display: flex; gap: 6px; flex-wrap: wrap; margin: 10px 0; }}
.badge {{ display: inline-block; padding: 3px 7px; border-radius: 999px; font-size: 12px; }}
.badge.table {{ background: #e7f0ff; color: #134b8a; }}
.badge.extra {{ background: #f2ece2; color: #6b4a16; }}
.flag {{ display: inline-block; padding: 4px 7px; border: 1px solid #d9dee7; border-radius: 6px; background: #fbfcfd; }}
.cols {{ display: grid; grid-template-columns: minmax(320px, 0.85fr) minmax(420px, 1.15fr); gap: 16px; }}
.evidence-block {{ border-top: 1px solid #eef1f5; padding-top: 7px; }}
ul {{ margin: 4px 0 8px 18px; padding: 0; }}
pre {{ overflow: auto; max-height: 460px; padding: 10px; background: #111827; color: #e5e7eb; border-radius: 6px; font-size: 12px; line-height: 1.4; }}
details {{ margin-top: 10px; }}
.hidden {{ display: none; }}
@media (max-width: 1000px) {{ .cols {{ grid-template-columns: 1fr; }} .card-head {{ flex-direction: column; }} }}
</style>
</head>
<body>
<header>
  <h1>Manual Motif Audit Dashboard</h1>
  <div class="controls">
    <label>Motif <select id="motif"><option value="">Any</option>{motif_options}</select></label>
    <label>Distribution <input id="dist" placeholder="e.g. poisson"></label>
    <label><input type="checkbox" id="top10"> top10 only</label>
    <label><input type="checkbox" id="final"> final only</label>
    <label><input type="checkbox" id="firstCluster"> first in cluster only</label>
    <button id="reset">Reset</button>
  </div>
</header>
<main>
  <div class="summary"><span id="shown"></span> shown out of {len(samples)} samples. Review one representative per cluster first, then inspect disagreements.</div>
  {''.join(cards)}
</main>
<script>
const cards = [...document.querySelectorAll('.card')];
const firstByCluster = new Set();
for (const card of cards) {{
  const data = JSON.parse(card.dataset.record);
  if (!firstByCluster.has(data.cluster)) {{
    firstByCluster.add(data.cluster);
    card.dataset.firstCluster = "true";
  }} else {{
    card.dataset.firstCluster = "false";
  }}
}}
function applyFilters() {{
  const motif = document.querySelector('#motif').value;
  const dist = document.querySelector('#dist').value.toLowerCase();
  const top10 = document.querySelector('#top10').checked;
  const finalOnly = document.querySelector('#final').checked;
  const firstCluster = document.querySelector('#firstCluster').checked;
  let shown = 0;
  for (const card of cards) {{
    const data = JSON.parse(card.dataset.record);
    const okMotif = !motif || data.motifs.includes(motif);
    const okDist = !dist || data.distribution.toLowerCase().includes(dist);
    const okTop = !top10 || data.top10 === "True";
    const okFinal = !finalOnly || data.final === "True";
    const okCluster = !firstCluster || card.dataset.firstCluster === "true";
    const visible = okMotif && okDist && okTop && okFinal && okCluster;
    card.classList.toggle('hidden', !visible);
    if (visible) shown += 1;
  }}
  document.querySelector('#shown').textContent = shown;
}}
for (const el of document.querySelectorAll('select,input')) el.addEventListener('input', applyFilters);
document.querySelector('#reset').addEventListener('click', () => {{
  document.querySelector('#motif').value = '';
  document.querySelector('#dist').value = '';
  document.querySelector('#top10').checked = false;
  document.querySelector('#final').checked = false;
  document.querySelector('#firstCluster').checked = false;
  applyFilters();
}});
applyFilters();
</script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sample_dir",
        type=Path,
        help="Directory containing sample_100_policy_motif_labels.csv and policies/.",
    )
    args = parser.parse_args()
    sample_dir = args.sample_dir.resolve()
    samples = read_samples(sample_dir)
    out_dir = sample_dir / "review_dashboard"
    out_dir.mkdir(parents=True, exist_ok=True)

    cluster_rows, cluster_id_by_hash, cluster_size_by_hash = build_cluster_rows(samples)
    queue_rows = build_review_queue(samples, cluster_id_by_hash, cluster_size_by_hash)
    write_csv(out_dir / "equivalence_clusters.csv", cluster_rows)
    write_csv(out_dir / "review_queue.csv", queue_rows)
    (out_dir / "review_dashboard.html").write_text(
        build_html(samples, cluster_id_by_hash, cluster_size_by_hash),
        encoding="utf-8",
    )
    print(f"samples,{len(samples)}")
    print(f"clusters,{len(cluster_rows)}")
    print(f"dashboard,{out_dir / 'review_dashboard.html'}")
    print(f"clusters_csv,{out_dir / 'equivalence_clusters.csv'}")
    print(f"review_queue_csv,{out_dir / 'review_queue.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
