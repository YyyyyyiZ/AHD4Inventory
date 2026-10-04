# Exact DP benchmark: four primary perishable-inventory instances

This is a classical OR benchmark, not an AIPS result. No LLM calls were made.
Final test seed 17094001 has not been accessed. Policy files are frozen in `freeze.json`.

| CV | FIFO share | IP cap | States | Gain lower bound | Gain upper bound | Independent simulation mean |
|---:|---:|---:|---:|---:|---:|---:|
| 1.5 | 0.0 | 17 | 5985 | 233.89939176435 | 233.89939177201 | 234.514844 |
| 1.5 | 0.5 | 16 | 4845 | 203.62065523986 | 203.62065524719 | 203.627083 |
| 2.0 | 0.0 | 14 | 3060 | 263.48379673368 | 263.48379674366 | 263.709635 |
| 2.0 | 0.5 | 14 | 3060 | 234.11681376909 | 234.11681377696 | 233.711198 |

All states `(age0,age1,age2,pipeline0)` with nonnegative integer components and sum at most the common cap are enumerated. Every feasible integer order is considered. FIFO service precedes LIFO service; remaining oldest stock expires; other inventory ages; prior pipeline stock arrives fresh; the new order becomes next period's pipeline.

Transition probabilities collapse each independent AER demand at current on-hand stock using exact distribution survival probabilities. No demand-tail truncation is used in the MDP. Expected lost units are `4 - E[sold]`, preserving tail shortage cost. Thus the only numerical approximations are floating-point arithmetic and the stopping tolerance.

Relative value iteration stops when the span of `T(h)-h` is below 1e-8. Its minimum and maximum give numerical lower and upper average-cost bounds. The reported intervals are numerical Bellman residual certificates, not interval-arithmetic proofs. The stationary table policy attains the upper bound.

Cross-checks compare eight states per scenario against direct summation over a long PMF through the separate simulator. Largest transition distribution L1 difference: 3.53e-13; largest expected-stage-cost difference: 6.39e-10. A short 3-path test per scenario confirms the Numba table policy and Python callback produce exactly identical path costs and components. Independent validation uses 64 paths, burn-in 500, 6000 measured periods, seeds 17096001..17096004. All four 95% simulation CIs contain their DP gain intervals.

Run from repository root:

```bash
.venv/bin/python -m examples.inventory.overnight_search.exact_dp solve
```

Only after the root experiment has frozen all methods and authorized opening the common test:

```bash
.venv/bin/python -m examples.inventory.overnight_search.exact_dp test --test-authorized
```

The test command uses the common seed 17094001, 128 paths, burn-in 500, and 3000 measured periods, separately for each scenario. Raw per-path costs and components are retained for paired comparisons. Any finite-test difference from the DP average-cost gain is simulation variation and initialization effect, not a violation of the DP bound.

For one scenario, `policy.npz` stores `theta`, `actions`, `states`, `base`, and `bias`. Load its `theta` and call the shared `perishable.evaluate` with `exact_dp.table_policy` to reproduce the table policy. `result.json` records model and source hashes, certificate, all cross-checks, and independent validation paths.
