# Exact per-objective action memoization diagnostic

Recommendation: this is worth integrating prospectively into newly started final-refit/test numerical worker calls, using the same option for every deterministic numeric policy. Do not change already-frozen policy sources, theta vectors, objective samples, budgets, optimizer seeds, or structure-search evaluation. Existing running workers remain unaffected.

All evidence below uses selected SOURCE/TRAIN coefficients and fresh diagnostic seeds 98713011–98713014. No final test file was read. One process ran at nice level 10; no paid calls and no active runner edits were made.

## Correctness evidence

- 128,000 period-level cached raw actions were checked against direct policy evaluation, across two selected methods, four scenarios, and five parameter vectors per scenario (source initial, training fitted, and three random bounded vectors). All comparisons were exact.
- Every per-path cost and waste/lost/order metric was exactly equal on these diagnostic paths and on the 32-path × 1000-period benchmark paths.
- Both methods passed a full 33-evaluation differential-evolution run with the same seed 98713014: every proposed parameter vector and objective value in the trajectory matched, as did final theta, final cost, and nfev. This used fresh 4-path × 200-period diagnostic tapes on m5/CV2/f0.5.
- Four sparse-cache cases additionally forced the cache limit to two entries. Cache saturation correctly fell back to direct calls with unchanged raw actions, path costs and metrics.

## Performance

Each row uses the saved training-fitted parameter vector. Speed is the ratio of median CPU time across three alternating original/cached calls; every cached objective allocates a fresh cache. Compilation is excluded, cache setup is included. Hit rate and speedup depend on the policy and sample length, so these are not universal bounds.

| Method | Scenario | CPU speedup | Hit rate | Unique states | Cache buffers |
|---|---|---:|---:|---:|---:|
| evolution_r2 | perish_m3_L2_cv1.5_f0 | 399.61× | 99.94% | 18 | 0.801 MiB |
| evolution_r2 | perish_m3_L2_cv1.5_f0.5 | 558.77× | 99.94% | 18 | 0.637 MiB |
| evolution_r2 | perish_m5_L2_cv2_f0 | 7.18× | 86.11% | 4446 | 1.000 MiB |
| evolution_r2 | perish_m5_L2_cv2_f0.5 | 10.24× | 89.58% | 3334 | 1.000 MiB |
| evolution_r3 | perish_m3_L2_cv1.5_f0 | 83.85× | 99.46% | 173 | 0.801 MiB |
| evolution_r3 | perish_m3_L2_cv1.5_f0.5 | 113.34× | 99.67% | 105 | 0.637 MiB |
| evolution_r3 | perish_m5_L2_cv2_f0 | 10.63× | 92.27% | 2475 | 1.000 MiB |
| evolution_r3 | perish_m5_L2_cv2_f0.5 | 11.51× | 92.03% | 2549 | 1.000 MiB |

Diagnostic worker peak RSS, including Python/Numba/compiler and benchmark arrays: 235.2 MiB. Successful run wall time: 44.0 seconds.

## Determinism and memory conditions

The validated policy subset permits only fixed numerical operations: whitelisted math/numpy functions, numerical builtins, local loops, immutable numeric module constants, and local working-array mutation. It excludes random/time/network/file functions, global/nonlocal statements, dynamic calls, arbitrary module attributes, external mutable state, and recursive/helper functions. The currently selected policies have been inspected and use only deterministic arithmetic and local arrays. This cache must not be generalized to an arbitrary Python Baek callable without a separate determinism guarantee.

The key encodes age followed by pipeline in radix cap+1. Simulator states are nonnegative integers with total inventory position <=cap, so each digit is in range and the key is injective. The wrapper requires finite cap and (cap+1)^dimension <= int64 max; unsupported cases must use the original kernel, not truncate keys. Fixed scenario parameters, theta, and policy are not included in the key because the entire cache is recreated inside every objective call.

A raw finite policy action is cached before common clipping/rounding. Cache misses still pass fresh copies of both state arrays. Reusing the raw result therefore preserves the original numerical operation order for all remaining projection, transition, cost, and metric arithmetic.

Small key domains use a float64 direct-index array, capped at 524,288 slots (=4 MiB). Larger domains use a multiplicative hash table with linear probing and explicit full-key equality; hash collisions cannot alias states. Sparse insertion stops at at most 100,000 entries, and a power-of-two table has at least twice that permitted occupancy. Its largest allocation is 262,144 int64 keys plus float64 values (=4 MiB total). Saturation leaves empty probe slots and falls back to direct evaluation for uncached states. The 4 MiB bound covers cache array data, with only constant-sized Python/NumPy object headers beyond it; simulator paths and compiler memory are separate.

Current benchmark cases use 0.64–1.00 MiB cache buffers. For a uniform refit/test integration, record cache mode, cache buffer size and whether fallback occurred if feasible. The simulator transition count and optimizer nfev should retain their existing meanings; fewer expensive policy evaluations are an implementation acceleration, not fewer sampled transitions.

## Integration boundary

Implementation is isolated in examples/inventory/overnight_search/memoization_diagnostic.py. The trusted kernel can be copied into the worker prelude with the corresponding bounded configuration routine. Enable only on an explicit final-refit/test flag, or an auditable whitelist of the four already-fixed final-refit/test seeds if old running parents cannot supply a new flag. Keep discovery and validation evaluators unchanged, and record the prospective implementation change. Do not restart completed fits solely to change this acceleration: the whole-objective and optimizer-trajectory checks support retaining their existing scientific records.

These checks establish exact equivalence on the inspected deterministic policies and sampled inputs, plus the key/cache construction argument. They do not justify silently memoizing external stateful or randomized policies.

## Integrated-worker sandbox check

After the root integrated the kernel, a separate isolated-prelude check compared cache-disabled and cache-forced calls to the actual `run_numeric_job`. It used only diagnostic seed 98714011, two selected methods, both a dense-cache m3 scene and sparse-cache m5 scene, and 17 optimizer calls per scenario. Every final parameter vector, cost, nfev, path cost, metric, cap, source/structure hash, parameter declaration, and import-normalization record matched exactly. The actual OS sandbox completed in 13.38 seconds. Selector override occurred only in the scratch prelude; active source was unchanged. See `sandbox_parity.json` and `memoization_sandbox_check.py`.
