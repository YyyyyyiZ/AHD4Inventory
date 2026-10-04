# Stationary autocorrelated inventory demand dataset

The complete dataset was generated before any policy outcome was evaluated. Train, validation and test streams are disjoint; no scenario will be omitted because of its winner.

## Files and use

Each scenario has `train.npz` (50 paths), `validation.npz` (128), and `test.npz` (1000). Every path has 1000 periods plus one preceding observed demand. Fields: `demands`, `lead_times`, `initial_last_demand`, `metadata_json`. Load with `numpy.load(..., allow_pickle=False)`.

For steady evaluations use demand periods 500:500+H, after simulating periods 0:500. For cold starts use 0:H from zero inventory and an empty pipeline. H is 50, 100, 200, or 500. Do not skip simulation of the burn-in. Use the same frozen rule across all H in the primary comparison.

## Model

All scenarios have the exact continuous Exponential(mean=100) stationary marginal. There is no integer rounding. Holding cost is 1 and lost-sales cost is 2 per unit per period.

- iid: Gaussian latent correlation zero.
- AR+: Z starts N(0,1), Z_t=0.8 Z_(t-1)+sqrt(1-0.8²) epsilon_t; D_t=-100 log(1-Phi(Z_t)).
- AR−: same construction with latent rho=-0.6.
- regime: stationary equally likely low/high state, stay probability 0.95; U_t=(S_t+V_t)/2, V iid Uniform(0,1), D_t=-100 log(1-U_t).
- Fixed lead is 6; random lead is 3 or 9 with equal probability, independent by calendar period and independent of demand.

Latent rho is not Pearson demand correlation. The regime construction has demand ACF(k)=ln(2)²×0.9^k. Demand is stationary from the initial observation, without a zero-state transient. Fixed/random lead variants share identical demand paths, isolating the lead-time change.

## Information and timing

Receive old orders; observe current lead quotation; place current order; realize demand; charge ending-inventory holding and lost-sales costs. Current quotation is known before ordering. Orders may overtake; existing pipeline buckets contain amounts due in 1,...,maxLead−1 periods. All methods observe the complete preceding demand, including unmet demand, and know the generator parameters. They never see current/future demand or future lead quotations. There is no policy clock or horizon input.

## Training-set diagnostics

| Scenario | Mean | SD | Demand lag-1 ACF | Demand lag-5 ACF |
|---|---:|---:|---:|---:|
| exp_iid_fixed6 | 100.25 | 99.58 | -0.005 | 0.003 |
| exp_ar_pos08_fixed6 | 101.00 | 100.96 | 0.769 | 0.288 |
| exp_ar_neg06_fixed6 | 99.70 | 99.70 | -0.424 | -0.058 |
| exp_regime095_fixed6 | 100.17 | 100.04 | 0.428 | 0.277 |
| exp_iid_random3_9 | 100.25 | 99.58 | -0.005 | 0.003 |
| exp_regime095_random3_9 | 100.17 | 100.04 | 0.428 | 0.277 |

Array hashes and file hashes are recorded in `dataset_manifest.json`; all split diagnostics are in `dataset_diagnostics.json`. Diagnostics are descriptive generator checks, never a filter based on policy performance.
