# Numerical evaluation corrections (September 2026)

The current code and canonical result files include these corrections. New runs do
not require a follow-up correction script. For self-contained commands to check
or re-evaluate the saved results without new LLM queries, see
[REPRODUCING.md](REPRODUCING.md).

## Lost-sales inventory

The simulators retain all arriving stock; the old on-hand grid bound is diagnostic,
not a disposal rule. Ordering costs are included. The benchmark tuner searches
stable constant and mixed-order policies, both adjacent mixed-order intervals,
and a refined integer stock grid for each capped-base-stock order cap. The
62 main/holdout benchmark cells were retuned and 654 saved policy evaluations were
replayed. Canonical evaluation rows and benchmark caches carry
`evaluation_version: unbounded-stock-v2`.

The LLM programs were unchanged. Each replay row includes the recorded scoring
protocol, cost and confidence interval, stock-bound diagnostics, and the
`policy_snapshot` identifying the constructed callable and its runtime. The
snapshots are included under `inventory_lost_sales/results/frozen_policies/`.
Original query/setup timing fields were retained; replay construction times are
stored separately in the snapshot metadata. `replay_saved.py inventory` reloads
these same objects and uses the recorded scoring streams, so no historical audit
folder or intermediate repair output is needed to check the current results.

## N-model queueing

Policies are evaluated by sparse stationary balance, and the comparator is computed
by sparse policy iteration. Costs and gaps must converge across N=600 and N=800;
nonconverged policies are not assigned a converged optimality gap. The evaluator
also records boundary probabilities. Current records in
`queueing/results/exact_eval.jsonl` carry `nmodel-converged-v2`.

Constructed policy snapshots and their portable action grids are shipped in
`queueing/results/frozen_policies/`; comparator grids are in
`queueing/results/dp_policies/nmodel_grids/`. `replay_saved.py nmodel` checks their
stationary costs and convergence without reconstructing a randomized policy.
The current runners save construction snapshots, but the older reentrant-line
simulation records were not retrospectively rerun with that construction protocol.

## Nested logit

Per-nest caps use `ceil(n * cap_rate)`, as in the benchmark, instead of rounding to
the nearest integer. All 48 affected L1 queries were replaced, while the saved L2
programs were re-evaluated without further model calls. Corrected canonical files
are used directly by the table generators. The original archives, replacement
query records, and the historical repair workflow are documented in
[assortment/results/nl_cap_correction/README.md](assortment/results/nl_cap_correction/README.md).
That historical workflow is not a prerequisite for running the current code.

## Validation

Regression tests cover stock conservation and cost accounting, stable benchmark
rates, compiled/Python simulator agreement, benchmark-search regression cells,
queue stationary balance and convergence, construction snapshot reuse, cap
rounding, and result selection. The release includes the additional replay tests
and a file manifest. Commands are in [REPRODUCING.md](REPRODUCING.md).
