# Baek-style perishable inventory comparator

Three independently prompted `openai/gpt-5.6-sol` L2 design sessions, high reasoning. Each session may use 3,600 seconds of Python computation and 50 tool calls. The three sessions share an independent **$12 hard API allocation**, which is part of the parent experiment's $50 ceiling. Unresolved paid requests retain their full upper-bound reservations.

The frozen [prompt](prompt.txt), [helper source](trusted_prelude.py), and [manifest](manifest.json) specify the experiment. Per-instance `design(params)` returns a stationary `policy(age,pipeline)`; parameters describe the same finite perishable family given to the competing structural search. Full mathematical demand laws, inventory projection, event order, and costs are common. The exact independent FIFO/LIFO two-moment mixture demand law is available in the helper source. Demand CV is ordinary standard-deviation/mean; this is a disclosed interpretation, not a claim of exact reproduction of legacy numerical tables.

All sessions receive the common simulator, demand generator, and 256-evaluation differential-evolution helper. Numba acceleration is additionally available to match the numerical evaluation available to the competing method. No policy-family hint or existing policy source is given. There is no parameter-count restriction. Returned designs may instead use their own numeric algorithms, simulations, or exact methods. The 30-second setup target is soft, with a 600-second guard during independent scoring.

`training_demands(params)` provides the same eight paths, 200 burn-in periods and 512 scored periods, seed 17091001, used by the parent screening experiment. A design session may generate other samples within its budget. Validation and test seeds and tapes are absent from the generation sandbox. Tool-session output labeled "test" by a model refers to its own self-generated development streams, not the parent's final holdout.

`sessions/l2_r1`, `l2_r2`, and `l2_r3` retain all request/tool journals, final outputs, source, and actual costs. The main comparison must retain all valid draws without selecting the worst or replacing valid but poorly performing draws. The final evaluation measures every method on identical caller-supplied demand tapes. An interrupted budget or network session is an incomplete comparator, not a poor policy score.

Read-only status:

```text
.venv/bin/python -m examples.inventory.overnight_search.baek_perishable status
```

The callable `score_code(code, params, demands, burnin=..., run_dir=..., timeout=...)` in `examples/inventory/overnight_search/baek_perishable.py` evaluates arbitrary submitted source inside the same filesystem/network sandbox. It returns path costs, waste/lost/order components, setup/score times, and the evaluation backend. Final policy code lives in a separate module namespace from the scoring tapes; Numba compilation is optional, with unrestricted Python fallback.

The paid-request accounting tests cover uncertain charges surviving restart, an interrupted request with no log retaining its reservation, and recovery from a durable response written before settlement. The isolated scorer has been cross-checked against the independent scalar reference on identical demands.
