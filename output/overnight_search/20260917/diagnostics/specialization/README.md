# Scenario specialization diagnostic

Conclusion: preserve the active evaluator. Literal scenario binding passed the sampled parity checks, but provided no consistent speed gain; it is not a useful acceleration for these two policies on this loaded machine.

Only selected source/training coefficients and fresh diagnostic seed 98712011 were used. No final test file was read. One process ran at nice level 10. The transformation removes mu/cv/f/L arguments and inserts their typed literal assignments at function entry, leaving subsequent local reassignment intact. It uses the exact current validator and bounds-checked Numba compilation; optimizer/evaluator/protocol files were not changed.

Across two methods and four scenarios, 4,840 state/parameter action comparisons were bit-identical before clipping. All 320 path/parameter costs and all waste/lost/order metrics were bit-identical (8 paths × 5 parameter vectors × 8 method/scenario pairs, each 250 periods with 50 burn-in). The vectors included source initialization, saved training fit, and three random bounded vectors. This verifies the entire sampled simulation objective, not universal floating-point equivalence or a full optimizer replay.

| Method | Scenario | Wall speedup | CPU speedup |
|---|---|---:|---:|
| evolution_r2 | perish_m3_L2_cv1.5_f0 | 0.987× | 1.030× |
| evolution_r2 | perish_m3_L2_cv1.5_f0.5 | 1.337× | 1.108× |
| evolution_r2 | perish_m5_L2_cv2_f0 | 1.111× | 0.974× |
| evolution_r2 | perish_m5_L2_cv2_f0.5 | 0.922× | 0.952× |
| evolution_r3 | perish_m3_L2_cv1.5_f0 | 0.265× | 0.579× |
| evolution_r3 | perish_m3_L2_cv1.5_f0.5 | 1.187× | 1.056× |
| evolution_r3 | perish_m5_L2_cv2_f0 | 0.944× | 0.897× |
| evolution_r3 | perish_m5_L2_cv2_f0.5 | 0.887× | 0.803× |

Each timing is the median of five alternating original/specialized objective evaluations, excluding compilation. Values above one favor specialization. CPU time excludes time scheduled to other workers; CPU frequency and thermal contention can still vary.
- evolution_r2: equal-work aggregate CPU ratio 1.012×.
- evolution_r3: equal-work aggregate CPU ratio 0.852×.

A first wall-only run is retained in result_first_wall_only.json; its apparently favorable pure-LIFO numbers did not survive the CPU-time follow-up. The added per-scenario compilation burden and weak/inconsistent runtime benefit favor leaving active final fits untouched. No fitting budget, parameter vector, source hash, or scientific policy was changed.

CPU-time follow-up wall duration: 42.3 seconds.
