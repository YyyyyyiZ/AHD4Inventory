# Overnight implementation audit

Scope: primary `m=3/4/5` and extended `m=7/8` perishable experiments under `examples/inventory/overnight_search/`. This is an implementation and synthetic-fixture audit, performed before final testing. It did not open real final-test result files, generate their demand tapes, inspect credentials, or make paid API calls. It is not a certification of the eventual empirical result or the current dollar total.

The main comparison computes the mean of all three generated policies for each arm, retains the full scenario grid, and uses paired demand-path bootstrap intervals conditional on those three policies. I found no demonstrated false-win arithmetic bug. The concrete defects below were found and corrected before final testing.

## Findings and corrections

| Finding | Consequence | Correction and evidence |
|---|---|---|
| Extended `group_summary.csv` omitted `generations` and `paths`, unlike the primary schema. | A complete extended report could produce a comparison plot with every principal group marked unavailable. | `extended.report_extended` now writes the primary-compatible group schema, including generation count, path count, and best/worst generation costs. A synthetic complete 8-scenario report reproduced **0/32** accepted plot cells before correction and **32/32** after correction. |
| `search.candidate` wrote new source files before returning an existing, unchecked `fit.json`. | Reusing a directory with changed source silently paired the old evaluation with newly overwritten source files. | Cached fit code, `source.json`, and `policy.py` must all match before any write. Four synthetic cases cover unchanged reuse and each mismatch; rejected cases preserve file bytes and modification times. |
| `baek_perishable.generate` defaulted its ledger to the run directory, even when an extended run had an existing shared allocation. | A restarted extended invocation missing `--budget-dir` could create an additional USD12 pool while reports read only the original pool. This was a concrete restart bug, not evidence that the actual launch overspent. | The Baek audit owner added `resolve_budget_directory`: saved allocation is immutable, a conflicting explicit directory is rejected, and the known extended run defaults to and requires the original Baek ledger. Allocation resolution occurs before credentials or POST. The owner reported six passing budget/source tests and confirmed that phase 2 had not started when corrected. |
| The generation prompt permits math/numpy imports without a scope restriction, but the numerical validator rejected a leading function-local `import math`. | Eligible sources could be marked invalid because of harness syntax rather than policy quality; root identified primary `best_of_n_r2` and `best_of_n_r3`, candidate `06_0`. | Added `normalization.py`: only allowed leading numerical imports after an optional docstring are hoisted in the AST. Conditional/nonleading imports remain rejected. Ambiguous alias rebinding is not normalized. Raw source, raw SHA256, assignment line numbers, OPT_PARAM comments, and parameter order are preserved. Metadata records each moved import. |
| During the import-metadata edit, a worker could read the new `numeric_job.py` while its parent still used the old validator prelude. | A valid training candidate could finish scoring and then fail on the harness return field `prepared['import_normalization']`. A read-only training-fit scan found exactly one such failure: extended `one_query_r2/candidate_00_7`; none in primary at that scan. | The field now uses `.get(..., [])` for old-prelude compatibility. The neutral repair recognizes this precise terminal KeyError only when the traceback identifies `run_numeric_job` and that prepared-field access. Other KeyErrors remain failures. |

The import correction is applied to fresh numerical evaluators through `evaluator.prelude`. `numeric_job` records raw code SHA256 and import-normalization metadata; `.get` preserves compatibility with evaluator processes already imported before the correction. Existing source files and LLM response journals are not rewritten.

### Repairing earlier import-scope failures

Run the following in fresh processes after all nine searches for the specified profile have completed:

```bash
.venv/bin/python -m examples.inventory.overnight_search.repair_imports --profile primary --apply
.venv/bin/python -m examples.inventory.overnight_search.repair_imports --profile extended --apply
```

Without `--apply`, the command reports its plan without evaluating or editing records. The repair:

1. Requires the exact nine arm/repetition pairs, matching prospective settings, no global numerical freeze, and no final-test output. A selection for an affected arm blocks correction; unrelated selections/refits are allowed.
2. Locates every recorded rejection containing `Imports must be at module scope`, or the precise transient metadata KeyError described above, verifies raw source provenance, and archives the original failed fits and affected completed-pool records. Each repair records its specific reason.
3. Re-evaluates unchanged code using **the original** training paths, seed, optimizer ceiling, and worker timeout: primary 256 objective calls/240 seconds; extended 1024 calls/900 seconds.
4. Replaces only the affected fit and completed-pool entries, recomputes that pool's training winner, and records original/corrected hashes and elapsed time. It never makes a model call or replays evolution feedback. Thus any historical feedback already given remains historical; this is a harness correction, not a restarted search.
5. Reuses an already recorded correction after interruption and avoids evaluating successfully corrected candidates again. Repaired candidates that remain invalid are still failures.

The audit implemented and tested this command but did **not** execute it on the real experiment directories. Whether each real profile has completed repair is an operational fact to check before selection; implementation readiness alone does not establish completion.

Synthetic verification covered 320 identical original/transformed policy actions, five non-neutral or disallowed import examples, original parameter line numbers and hashes, two affected arms, preservation of an unrelated selection, archives, idempotence, and the post-freeze guard. A separate isolated evaluator check used two short synthetic paths with seed `951951` and a four-call optimizer ceiling; it confirmed the metadata and parameterized evaluation end to end. No final-test seed was used.

The follow-up synthetic check covered six negative transient-error matches, repaired one scope error and one precise metadata error under the original extended training ceiling/timeout, and confirmed that two other KeyError failures were byte-for-byte unchanged. A second invocation did not rescore repaired candidates. The real fit-directory scan inspected training failures only; it did not inspect final-test files.

## Budget and failure handling

The framework uses a single USD35 ledger; the extended client explicitly points to the original framework ledger. Primary and extended Baek sessions now share the original USD12 ledger. The configured aggregate commitment is USD47, with USD3 unallocated under the user's USD50 authorization. Framework reservations use a file lock; Baek reservations use an in-process lock plus a process-wide generator lock. Requests reserve their conservative bound before submission. Unknown transport charges and missing authoritative costs retain reservations. Recorded responses can reconcile only their matching Baek reservation. No automatic paid transport replay was found.

This source review verifies the intended accounting mechanics, not the actual receipts. Final expenditure must be taken once from the two shared ledgers, including unresolved reservations; extended cumulative totals must not be added a second time. A provider charge exceeding a reserved bound is detected after the response, so any such event remains an accounting exception requiring explicit disclosure.

Invalid numerical candidates remain in completed pools with `valid=False`; the shared initial baseline is an explicit fallback. A response with no extractable code has a separate invalid record and still consumes its paid request/candidate opportunity. Worker timeout or scoring failure is not converted into a zero-cost result. Baek scoring records per-case failures and incomplete coverage, and the report withholds a complete success claim unless all principal repeats/scenarios are present. A validation/refit exception stops completion rather than silently choosing a different candidate using test results.

Successful numerical jobs record objective counts, wall time, and simulated transitions. Earlier invalid jobs do not preserve full partial objective counts or elapsed time; consequently these records do **not** establish equal realized total compute. The import-repair receipts do retain their own elapsed time, including failures.

## Freeze gates and provenance

The latest primary `evaluate_search.main` now requires all three Baek policy files and seals their SHA256 values **before** constructing any final-test job, after numerical structures and fitted parameters are frozen. `score_baek` requires the numerical seal, verifies the Baek source seal, and preserves the original seal timestamp. Extended evaluation already gates on the exact nine searches, its numerical freeze, and all three Baek sources. Neither gate performs adaptive selection from final scores.

The Baek generator freezes prompt and trusted-helper hashes and checks both before generation. Final numerical policy artifacts freeze raw code and fitted parameters. Numerical evaluation caches bind the full request, including code, theta, scenario settings, and seed. The import correction preserves raw source attribution and explicitly identifies its compiler-side transformation.

Two additional static resume hardening gaps were corrected at root's request; no stale real result was observed in this audit:

- Primary `score_baek` now requires an existing per-scenario cache's `code_sha256` and `test_settings` to match the frozen policy and current test request, as extended scoring already does. Newly written primary scores include both fields. Missing metadata is rejected, not guessed. Four synthetic negative cases covered altered code, altered settings, and absent metadata.
- Primary `evaluate_search` now requires the exact nine arm/repetition pairs as well as nine files. Four synthetic negative cases covered missing, extra, duplicated, and unknown-arm records.

Numerical cache request fingerprints do not include the trusted simulator/optimizer/validator source. Therefore raw policy hashes alone cannot prove that cached scores across a restart used identical evaluator semantics. Preserve the relevant source revision and disclose the import correction; do not silently change simulation or optimization semantics while reusing old cached scores. Baek scoring likewise reads the frozen helper file; retaining its manifest and unchanged content is necessary for provenance.

## What the comparisons can establish

The three numerical structure arms use the same optimizer implementation, per-candidate objective-call ceiling, and phase-specific demand paths. Primary one-query returns four candidates versus eight for independent generation/evolution; extended raises this to eight for all three and supplies the same initial baseline information. Failed or missing candidates and early optimizer convergence can reduce realized evaluations. Each successful fit also performs one scoring evaluation after optimization, counted by `transitions`; the advertised ceiling governs optimization calls, not this final rescore.

Baek retains full Python tool use, up to 50 tool calls and 3600 cumulative tool seconds, and a final design-stage guard of 600 seconds per scenario. These are different resources from numerical structure search. Its supplied helper exposes the optimizer, but the agent may choose another algorithm or simulation count. Both use the stated base model and reasoning effort, with different tool/API workflows. The extended 1 GiB per-worker RSS guard is shared, but this does not equalize total wall time, tokens, dollars, simulator calls, or setup compute. A result should therefore be called an equal-model comparison under disclosed resource limits, not an equal-compute comparison.

The optimizer ablation evaluates each selected structure with its emitted literal defaults and with externally fitted parameters, on common final paths. It estimates the value of coefficient fitting **for a structure selected by the tuned pipeline**. It is not a full rerun of structure search with the optimizer removed, and does not isolate an end-to-end causal optimizer effect.

`m=4`/`m=8` are withheld-feedback structure-transfer scenarios for the three numerical arms, followed by instance-specific coefficient refitting. Baek knows the public finite parameter family and may simulate any member or fit within `design(params)`. These are not unknown-parameter holdouts shared by every method. The extended report wording now states this explicitly; the model-audit owner is amending the primary wording.

The implementation correctly calls the baseline a **Baek-style L2 adaptation**. It changes the problem, supplies trusted simulation/optimization helpers, imposes explicit policy interfaces/resource limits, and uses the disclosed demand/cap convention. Three generated draws are repetitions of this adaptation, not a reproduction of the published experiment. The existing exact-DP benchmark and nested-logit replay remain OR/reference diagnostics and must not be credited as AIPS-generated improvements.

## Audit artifacts

The pre-fix schema/cache reproduction and post-fix synthetic checks used temporary directories only. The final import-normalization/repair fixture is under `/var/folders/b7/dlsj_scs5pxbrd6_69xztsmr0000gn/T/overnight_import_repair_synthetic_dw2pixie`; it contains fabricated results and must never be included in the research tables. All six current Baek source/budget unit tests, including the shared-allocation restart checks, passed in this audit. Modified Python modules also passed syntax compilation. No evidence from an unopened real final test appears in this document.


## Exact action memoization (2026-09-17 05:06 UTC)

Execution amendment 04 enables bounded exact state-action reuse only for the four frozen primary/extended refit and test request signatures. Search and validation keep the original evaluator. The cache is reset for every theta/scenario objective, stores the unrounded raw action, uses injective signed-int64 keys, and falls back to ordinary policy calls after sparse-cache saturation. Array storage is bounded by 4 MiB. The numerical AST permits no random calls, clock access, external mutable state or persistent policy memory; input copies preserve local mutation semantics.

The standalone diagnostic checked 128,000 raw actions and complete path costs/metrics, forced cache saturation, and two full 33-call differential-evolution trajectories, all exactly equal. A separate actual-sandbox check of both slow policies and dense/sparse scenarios reproduced theta, cost, nfev, path costs/metrics, caps, source hashes, parameter declarations and normalization metadata with 17 optimizer calls. Evidence is in `output/overnight_search/20260917/diagnostics/memoization/{result.json,sandbox_parity.json,README.md}`. No final-test data were accessed for either diagnostic.

Previously successful uncached fits are reused because the objective and optimizer trajectories are unchanged. Already-running jobs finish unchanged; later dispatches read the amended trusted source. New per-scenario checkpoint records retain hit/miss/configuration metadata even when an older parent omits those fields from its combined refit record. The source snapshot is preserved under `output/overnight_search/20260917/execution_sources/memoized_evaluator_v1/`. This improves execution time, adds no optimizer calls or paid requests, and does not establish equal compute between the numerical framework and Baek sessions.

Independent integration review recorded at **2026-09-17 05:10:34 UTC** confirms exact stage routing and the production 100,000-entry sparse-cache clamp. The actual isolated-worker parity evidence is [sandbox_parity.json](../output/overnight_search/20260917/diagnostics/memoization/sandbox_parity.json): both selected slow policies, both dense/sparse cases, 17 optimizer calls per case, and unchanged theta/cost/path metrics/source metadata. The [full diagnostic report](../output/overnight_search/20260917/diagnostics/memoization/README.md) also links the two exact 33-call optimizer trajectories. This integration audit used diagnostic seeds only; the subsequent, separately authorized primary-result provenance audit is documented in `overnight_primary_result_audit.md`.
