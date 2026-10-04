# Extended final-result provenance audit

Audit time: **2026-09-17T05:50:56.746693+00:00**. Scope: existing extended m=7/8 metadata and result records only. No policy execution, demand-tape generation, paid request, or strategy/selection/parameter change occurred.

**Status: pass; 2016 checks, 0 failures.**

Inspected 28 tuned/default numeric files, 224 numerical scenario rows (28,672 path costs), and 24 Baek case records.

The audit independently reconstructs each full numeric test-request SHA256 from frozen code/theta, complete scenario dictionaries, optimizer seed 1731 and prescribed **128 paths / 500 burn-in / 3000 scored periods / demand seed 18094001**. It also checks selected/origin/baseline source hashes, refit theta, literal defaults, compiled-structure hashes, parameter declarations, normalization metadata, caps, zero test nfev, scenario coverage and recorded transition counts.

Each Baek source is checked against its source seal, session hash and final code. All available per-case code hashes/settings and aggregate rows are checked; the frozen prompt/helper hashes are compared with the manifest. Extended aggregates do not themselves require a top-level policy hash: provenance is verified through every contained per-case hash and the separate source seal.

Largest path-mean discrepancy: 0; largest cost-versus-100×(waste+lost) discrepancy: 1.99e-13. These consistency checks do not rank methods or interpret statistical significance.

Limits: this verifies agreement among local saved artifacts, not an independent replay or externally timestamped history. Request fingerprints do not bind trusted evaluator/optimizer/compiler code or actual demand-tape bytes; no saved tape hash is verified here. The retained implementation snapshots, manifest and execution amendment remain necessary. This does not certify equal compute, spending, causal optimizer benefit, policy novelty or superiority.

Evidence: [result.json](../output/overnight_search/20260917/extended/diagnostics/extended_result_audit/result.json), including hashes of every inspected evidence file; [implementation audit](overnight_implementation_audit.md).
