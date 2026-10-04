# Overnight Baek audit — 2026-09-16

Read-only inspection of prior experiments and source, apart from this new note. No paid API requests. Existing work was preserved.

**Subsequent verification:** This note records the initial audit. The later independent nested-logit audit did obtain the corrected author repository, reproduced all 971 corrected cases, and identified the old capacity-rounding discrepancy. The initial source-access failure below is superseded by [overnight_nested_diagnostic.md](overnight_nested_diagnostic.md). New perishable experiments are documented separately; the conclusions about pre-existing inventory results remain unchanged.

## What is already established

**There is currently no saved inventory instance demonstrating a robust AHD advantage over a properly adapted Baek tool-enabled query.** The prior iid experiment goes the other way; the correlated experiment has useful difficult environments but did not run Baek on them.

`output/baek_comparison/20260915_first_round/report.md` reports all 18 original sessions valid, nine L1 and nine L2, producing 99 scenario policies. On fresh paths, L1 improves over historical AHD by 0.19%, 0.24%, and 0.58% on exponential/normal30/Poisson at L=6,p=2; L2 improves by 0.12%, 0.32%, and 0.50%. Across 20 historical-AHD scenarios, L2's mean improvement is 3.01%, median 0.88%. Across 30 scenarios every three-draw L2 mean is within 0.1% of or better than the trained classical comparator. Existing iid settings therefore offer little useful search leverage.

`output/correlated_inventory/20260916_stationary_priority/RESULTS_SUMMARY.md` is complete: 27 training chains, 720 scored windows, three repetitions. The following are cost per period at burn-in 500 and horizon 200, with all means taken across the three saved AHD draws:

| Environment | AHD | Adaptive PIL | AHD improvement against Adaptive PIL |
|---|---:|---:|---:|
| IID, fixed L=6 | 124.975 | 123.645 | −1.08% |
| AR latent rho=+0.8, fixed L=6 | 166.171 | 161.810 | −2.69% |
| AR latent rho=−0.6, fixed L=6 | 101.886 | 100.007 | −1.88% |
| Persistent regimes, fixed L=6 | 152.560 | 147.733 | −3.27% |
| IID, quoted L∈{3,9} | 139.946 | 131.992 | −6.03% |
| Persistent regimes, quoted L∈{3,9} | 153.126 | 147.791 | −3.61% |

The last environment is the most promising existing mechanism: AHD beats constant order by 5.88%, capped base stock by 4.37%, and the simple committed-only conditional PIL by 0.84%. But adaptive PIL and the alternative PIL+COP continuation still beat AHD. Treating the simple PIL as the strongest comparator would overstate the result.

The unrestricted-parameter rerun and adaptive-PIL-seed rerun are incomplete in their saved reports. The latter shows a 0.651% *training* improvement from the seed in the persistent-regime/random-lead environment, but no completed three-draw holdout comparison. It is not evidence of a test-set improvement. See `output/correlated_inventory/20260916_adaptive_pil_seed/adaptive_pil_report.md` and `output/correlated_inventory/20260916_unrestricted_params/parameter_comparison/report.md`.

## Verified Baek protocol and source availability

The paper is Jackie Baek, *LLMs Can Design Near-Optimal OR Algorithms*, arXiv:2608.27296v1. L1 gives exact instance parameters; L2 supplies a problem class and broad ranges. One query includes a complete Python tool session, with 3,600 seconds and at most 50 calls for inventory. Setup is asked to finish within 30 seconds; 600 seconds is the hang guard. Final policies may use stdlib, NumPy, and SciPy and may be randomized. Original deterministic lost-sales inventory uses known iid Poisson demand, integer bounded orders, and a long-run objective. Defective outputs may be regenerated from the same prompt; poor valid outputs are not selectively retried. These details are directly verified in the [paper and appendices](https://arxiv.org/html/2608.27296v1).

The paper links the [official anonymous code repository](https://anonymous.4open.science/r/llm-or-algorithms-F9F2/). Today the browser could not open that repository, and direct public raw-file requests returned HTTP 403. Consequently this audit does **not** independently verify the prior proposal's numerical-corrections claim or an upstream source hash. The local archived protocol and implementation are inspectable, and the paper itself was accessible.

The repository's prior comparison explicitly adapts orders to continuous, unbounded nonnegative values and uses 50 periods after L zero-demand setup periods. Those are disclosed deviations from the original paper. For tonight's new environments, a fresh L1 tool-enabled query with the correct dynamics is the most direct Baek comparison. Running an old iid-Poisson artifact unchanged on correlated demand would measure transfer failure, not the capability of Baek's design procedure.

## Reusable components and constraints

| Purpose | Existing implementation | Notes |
|---|---|---|
| Tool-enabled query | `examples/inventory/baek_comparison/harness.py` — `OpenRouterHarness`, `SessionConfig`, `RunBudget` | Accepts a custom problem prompt. Appends durable requests/responses, tracks tool time and uncertain charges. `run(prompt)` returns final source. |
| Isolated Python tools | `examples/inventory/baek_comparison/sandbox.py` — `PythonSandbox` | NumPy/SciPy available; no network or repository-data access. State does not persist between calls. |
| General current-state simulator | `examples/inventory/correlated_benchmark/environment.py` — `simulate_callable`, `simulate_compiled` | Arrival → quote/order → demand → cost; all due inventory preserved; allows order overtaking. |
| New reproducible data | `examples/inventory/correlated_benchmark/data.py` — `Scenario`, `generate_tapes` | Existing iid/AR/regime generators accept new persistence, lead support, and penalty parameters. Independent seeds; exact exponential marginals. |
| Strong classical families | `examples/inventory/correlated_benchmark/baselines.py` — `fit_baselines`, `evaluate_baseline` | Includes CBS, forecast CBS, conditional PIL, adaptive PIL, and random-lead continuation. |
| Existing AHD search | `examples/inventory/correlated_benchmark/evolution.py` — `run_evolution` | Original single-best-parent m2 loop; unlimited parameter count currently supported; SciPy L-BFGS-B. |
| Efficient train-only objective | `examples/inventory/correlated_benchmark/problem.py` — `TrainingProblem` | Cannot load test; caches structure and coefficients independently through `fast_policy.py`. |

Important integration details:

- The common interface is `compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time)`. Pipeline entry k−1 arrives in k future periods, up to max lead−1. Last demand is full demand, including unmet sales; the current order's lead quote is known before the decision. All methods must receive these same observations.
- The regime generator is intentionally observable: previous regime is exactly recoverable from last demand being above/below mean×log(2). It is not a hidden-state learning problem. AR last latent value is similarly recoverable from last demand.
- `fast_policy.prepare_policy` is a restrictive AHD numerical language: one function, no helpers/SciPy/mutable arrays. Baek output must not be rejected simply for using capabilities allowed by its protocol; use a general isolated callable scorer when needed.
- `OpenRouterHarness` currently has Sol-oriented price caps of $4/$15 per million input/output tokens. The correlated `BudgetedClient` has DeepSeek-oriented caps $0.50/$1.20 and a frozen single-model ledger. Changing model names alone is insufficient for a stronger backbone. Establish new runs/ledgers and explicit appropriate price ceilings; coordinate one global $50 ceiling across all paid paths.
- Existing optimization is L-BFGS-B with absolute finite-difference step 0.1 and default 15 iterations. Integer rounding and branch thresholds can create flat or nonsmooth objectives; different coefficient scales also make one absolute step unsuitable. A normalized bounded derivative-free/global search followed by local refinement is a meaningful optimizer variation, but its gain must be measured on fresh paths.

## Highest-value experiment tonight

1. Screen a **family**, using fresh train/validation seeds, around persistent regimes plus quoted short/long leads: regime persistence 0.90/0.97/0.995, L∈{1,12} or {3,9}, short-lead probability 0.25/0.5, p/h=2/5. These are hypotheses about interaction-driven difficulty, not predicted winners. Include fixed-L and iid controls. Existing generators and environment cover all these changes directly.
2. Take only one or two train/validation-selected families into expensive Sol sessions. Give Baek exact generators and 3,600-second/50-call tools; provide its training simulator or a precise equivalent specification. Do not hint a specific policy family. Save all valid draws.
3. On the same candidate structure, measure **raw coefficients → external optimizer** using common train paths. Then compare equal-model/equal-LLM-budget AHD with and without the optimizer. Also apply the optimizer to the Baek artifact when its coefficients can be extracted transparently. This directly asks whether the optimizer adds value beyond structure generation.
4. Freeze every selected policy and selection rule before generating a fresh confirmation set. Report paired path intervals and at least three independent model draws for finalists; keep the discovery sweep labeled exploratory. Compare against Adaptive PIL as well as Baek. A win over an old weak iid transfer baseline or an isolated worst Baek draw is not a convincing result.

For attribution, separate (a) model strength, (b) numeric optimizer, (c) number of model-generated candidates, (d) seed-policy knowledge, and (e) simulator evaluations. Any manually engineered successful policy remains a useful mechanism probe but should be labeled as such until the AHD generation path reproduces it.
