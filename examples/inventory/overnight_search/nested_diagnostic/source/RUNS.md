# Run records

Every LLM query in the paper is logged as one JSON line. A query record stores the exact prompt,
every turn (assistant text, reasoning summaries where the API returns them, tool-call counts,
latency), every sandbox cell (code, output, seconds, error/timeout flags), token usage including
reasoning tokens, the served model version, and the returned code. Level-2 files also hold one
`eval` record per evaluation instance (the returned algorithm run on that instance, with its
cost or revenue, confidence interval, and the benchmark values it is compared with). Records are
appended in the order they were produced; failed attempts are kept next to their reruns.

Reading a record: `python inventory_lost_sales/show_run.py <file.jsonl>` prints a query turn by
turn (reasoning summary, assistant text, code, output). Every `make_*.py` script regenerates its
table or figure from these files.

## Main experiments

| setting | level | models | instances | budget | files |
|---|---|---|---|---|---|
| Lost sales (det. + stoch. lead times) | 1 | sol, fable, 5.4, 5.1 | 26 per model | 3600 s, 50 calls | `inventory_lost_sales/results/l1_<model>.jsonl` |
| Lost sales, deterministic class | 2 | sol, fable, 5.4, 5.1 | 1 algorithm → 19 evals | 3600 s, 50 calls | `inventory_lost_sales/results/l2_det_<model>.jsonl` |
| Lost sales, stochastic class | 2 | sol, fable, 5.4, 5.1 | 1 algorithm → 7 evals | 3600 s, 50 calls | `inventory_lost_sales/results/l2_stoch_<model>.jsonl` |
| Dual sourcing | 1 / 2 | sol, fable, 5.4, 5.1 | 6 / 1 → 6 | 3600 s, 50 calls | `inventory_dual_sourcing/results/l{1,2}_<model>.jsonl` |
| Multi-echelon distribution | 1 / 2 | sol, fable, 5.4, 5.1 | 2 / 1 → 2 | 3600 s, 50 calls | `inventory_multi_echelon/results/l{1,2}_<model>.jsonl` |
| Assortment MMNL / NL / constrained | 1 | sol, fable, 5.4, 5.1 | 72 / 48 / 36 (stratified) | 900 s, 50 calls | `assortment/results/l1_{mmnl,nl,mmnl_c_guo}_<model>.jsonl` |
| Assortment MMNL / NL / constrained | 2 | sol, fable, 5.4, 5.1 | 3 algorithms each → 628 / 971 / 180 evals | 3600 s, 50 calls | `assortment/results/l2_{mmnl,nl,mmnl_c}_<model>.jsonl` |
| Constrained MMNL on the authors' 1,794 instances | 2 | sol, fable, 5.4, 5.1 | the same 3 algorithms re-evaluated | — | `assortment/results/guo_constrained/eval_<model>.jsonl` |
| Queueing (13 Dai–Gluzman instances) | 1 | sol, fable, 5.4, 5.1 | 13 per model | 3600 s, 50 calls | `queueing/results/six_l1_six_gpt-5.6-sol.jsonl` + `dg13_l1_<model>.jsonl` |
| Queueing, structural classes (criss-cross / reentrant line / N-model) | 2 | sol, fable, 5.4, 5.1 | 1 algorithm per class → 6 / 6 / 1 evals | 3600 s, 50 calls | `queueing/results/dg_l2_{cc,line,nmodel}_<model>.jsonl` |
| Queueing, broad multiclass-network class | 2 | sol, fable, 5.4, 5.1 | 1 algorithm → 13 evals | 3600 s, 50 calls | `queueing/results/dg_l2_general_<model>.jsonl` (sol: `six_l2_six_…` + `dg13_l2_…`) |
| Queueing stability | 2 | sol | 9 extra draws per class | 3600 s, 50 calls | `queueing/results/var10_l2_{qnet,cc,line,nmodel}_gpt-5.6-sol_b{1,2,3}.jsonl` |
| Queueing zero-compute rung | 2 | sol | 1 per class | 0 s | `queueing/results/ladder0_l2_<class>_gpt-5.6-sol.jsonl` |

`<model>` ∈ `gpt-5.6-sol`, `claude-fable-5`, `gpt-5.4`, `gpt-5.1`. The first valid level-2
algorithm per (model, class) is the one the paper reports; the others are the replicates used in
the stability analysis. `assortment/results/l1_mmnl_c_<model>.jsonl` are level-1 runs on our own
regenerated constrained pool (superseded in the paper by the runs on the authors' instances,
`l1_mmnl_c_guo_*`); they are kept for completeness.

## Robustness checks (gpt-5.6-sol)

| check | what | files |
|---|---|---|
| Zero query-time compute | lead-time sweep at level 1 (6 queries) and the deterministic class at level 2 (1 query), budget 0 s; assortment level 2, one query per family | `inventory_lost_sales/results/ladder0_l{1,2}_*.jsonl`, `assortment/results/ladder0_l2_*.jsonl` |
| Repeated draws | 10 level-2 queries per class (the campaign artifact(s) plus `var10_*`) | `*/results/var10_l2_*.jsonl`, `assortment/results/guo_constrained/eval_var10_*.jsonl` |
| Holdout instances | the main level-2 algorithms re-run on new instances | `*/results/holdout_l2_*.jsonl`, `holdout_*_benchmarks.json`, `holdout_*_references.json` |
| Web-search tool | level-2 queries with OpenAI's `web_search` tool attached (det. lost sales, MMNL, NL, constrained) | `*/results/websearch_l2_*.jsonl`, `assortment/results/guo_constrained/eval_websearch_*.jsonl` |

## Incidents (all preserved in the records)

- Four level-2 answers hit the harness's 16k output-token cap mid-answer (gpt-5.4 and gpt-5.1 on
  two classes each) and one gpt-5.1 level-1 answer hit it while dumping a policy table. The cap
  is invisible to the model, so these are harness-side; each was re-queried at a higher cap and
  the truncated attempt kept.
- Three assortment level-2 artifacts (one gpt-5.6-sol MMNL run that did not compile, one that
  returned the empty assortment everywhere, one gpt-5.4 constrained run that crashed on 16
  instances) are model-side failures; they are kept, flagged, and the next valid replicate is
  reported.
- One web-search lost-sales query ended in a provider connection error after an hour-long turn;
  the failed attempt is kept and the rerun (zero searches, same file) is the reported one.
- The first web-search constrained evaluation and the claude-fable-5 constrained evaluations were
  interrupted once by the file-sync layer zeroing an open file; the affected rows were
  re-evaluated (identical results) before the files were finalized.


## Queueing evaluation records

Criss-cross costs use fixed-policy relative value iteration on a finite chain.
The N-model uses sparse stationary balance for each policy and sparse policy
iteration for the comparator, with convergence checks across N=600 and N=800.
`exact_eval.jsonl` stores the evaluations and status, and `dp_policies/` stores the
comparators. Current N-model rows carry `evaluation_version: nmodel-converged-v2`;
only rows whose status is `ok` have a converged gap.

The reentrant-line instances use steady-state simulation (`evalss.py`), with the
protocol fields stamped on evaluation rows. `baselines_ss.jsonl` re-simulates
LBFS/cmu/MaxWeight/MaxPressure; `six_qgym_protocol.jsonl` and `qgym_native_*.jsonl`
are additional protocol checks (the latter require the optional QGym clone).
The older reentrant-line results predate construction snapshots. Their repeated
queries use a lighter simulation protocol than the main comparison.

Main and repeated-draw evaluations must remain separate. Select by model, instance,
policy kind, and (for repeats) source file and source index; do not simply take the
last row for an instance. `common/results.py` implements main-result selection,
and `queueing/exact_records.py` replaces only an identical logical evaluation.
Raw query logs preserve failures; current N-model repeat scores have ten valid
artifacts under the recorded construction/evaluation protocol.

## Numerical corrections and replay evidence

The current canonical inventory and N-model evaluation records contain the corrected
costs. Original query transcripts and generation/setup times are retained, while
re-evaluation details live in the scoring, evaluation-version and policy-snapshot
fields. Snapshot construction times describe the replay, not the original query.
The inventory release contains all 654 constructed policies needed for its saved
re-evaluations. N-model policies also have portable N=600/800 action grids.

Nested-logit correction records include the original archives, 48 replacement L1
queries, and L2 rescoring of unchanged programs. See
[NUMERICAL_CORRECTIONS.md](NUMERICAL_CORRECTIONS.md) for the changes and
[REPRODUCING.md](REPRODUCING.md) for commands. No historical correction workflow is
required before running the current simulators or generating the paper tables.
