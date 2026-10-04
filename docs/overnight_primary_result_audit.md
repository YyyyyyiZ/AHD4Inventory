# Primary final-result provenance audit

Audit time: **2026-09-17T05:12:55.082717+00:00**. Scope: existing primary m=3/4/5 result files only. No policy was executed, no demand tape generated, no paid call made, and no strategy/selection/parameter changed. Extended final results were not inspected.

**Result: all checked provenance and arithmetic records pass.** At this snapshot all 14 numerical artifacts had both tuned and literal-default scores (28 files), and all three Baek draws had all 12 per-case scores plus their aggregate files. There are no missing Baek cases to defer.

## Numerical records

- Numeric and Baek source seals both record 2026-09-17 05:08:44 UTC. All 14 frozen numeric code hashes match their code strings; all nine selected sources match their selected record and original candidate source, and all five baseline sources match their saved baseline source.
- Each frozen per-scenario theta equals its saved refit theta. All 28 complete test-request SHA256 values were independently reconstructed from frozen code, exact theta, full scenario dictionaries, optimizer seed 1731, and prescribed **128 paths, 500 burn-in periods, 3000 scored periods, demand seed 17094001**. Every fingerprint matches.
- Tuned test theta equals the numeric seal. Each untuned theta was independently recovered from the actual emitted OPT_PARAM assignment literals, in source order; it agrees with the numerical validator and every stored untuned result. In this snapshot all emitted literals also equal their declared initial metadata.
- Every test file has exactly the 12 expected scenarios, matching code/structure hashes, parameter declarations and import-normalization metadata. All test rows record nfev=0; each artifact records 12×128×3500=5,376,000 simulated transitions and the prescribed model cap.
- Across **336 numerical scenario rows and 43,008 stored numerical path costs**, every path list has 128 finite values. Recorded costs equal NumPy means of the stored paths exactly. The same arithmetic checks pass for the 36 Baek rows. The largest cost-versus-100×(waste+lost) discrepancy is only 1.71×10⁻¹³, consistent with floating-point summation.

| Selected artifact | Frozen candidate origin | Raw code SHA256 prefix |
|---|---|---|
| best_of_n_r1 | search/best_of_n_r1/candidate_04_0 | `8e9dd34b1949347a` |
| best_of_n_r2 | search/best_of_n_r2/candidate_01_0 | `bfd653f16e6f027f` |
| best_of_n_r3 | search/best_of_n_r3/candidate_00_0 | `ec14749905e06b55` |
| evolution_r1 | search/evolution_r1/candidate_00_0 | `6072521b20a07054` |
| evolution_r2 | search/evolution_r2/candidate_06_0 | `fbac27098cbeaefc` |
| evolution_r3 | search/evolution_r3/candidate_05_0 | `fa58f9c5afdd4661` |
| one_query_r1 | search/one_query_r1/candidate_00_0 | `a03a1470e7b68e9d` |
| one_query_r2 | search/one_query_r2/candidate_00_2 | `a6d54e4a544b496c` |
| one_query_r3 | search/one_query_r3/candidate_00_1 | `a0c600b34deb75f0` |

## Baek records

For each of the three draws, policy.py bytes match the Baek source seal, saved session code_sha256 and saved final_code. All 36 per-case records match that frozen source hash and the prescribed test settings above, contain 128 finite path costs, and have consistent means and cost components. Each aggregate is exactly the corresponding 12 per-case records and carries the correct policy hash and complete=True. The current frozen prompt and trusted_prelude.py hashes also match the primary Baek manifest.

## Limits and retained evidence

This is a consistency audit of saved evidence, not an independent simulation replication or a judgment about which method wins. Request hashes bind code, theta, scenario settings and seeds; they do **not** bind the trusted simulator/compiler/optimizer source or the actual generated demand tape. No tape hash is present in these numerical results, and this audit did not regenerate tapes. Full runtime provenance therefore also depends on the retained implementation snapshots, source audit and execution amendment 04; exact action-cache parity was checked separately on diagnostic data.

The seals are local JSON records, not externally timestamped signatures. This audit establishes agreement among the artifacts available at the snapshot, not an independent proof of their full chronological history. It also does not certify total spending, equal realized compute, uncertainty intervals, optimizer causality, or novelty of a policy.

Machine-readable evidence: [result.json](../output/overnight_search/20260917/diagnostics/primary_result_audit/result.json), containing 2874 checks, zero failed checks, full selected-source/request hashes, and SHA256 snapshots of every inspected evidence file. Earlier execution checks: [implementation audit](overnight_implementation_audit.md) and [isolated-worker parity](../output/overnight_search/20260917/diagnostics/memoization/sandbox_parity.json).
