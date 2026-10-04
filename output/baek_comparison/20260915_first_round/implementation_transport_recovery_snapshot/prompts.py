"""Pre-registered problem-only prompts for the Baek protocol adaptation."""

import json


FAMILIES = ("poisson", "normal", "exponential")

PROBLEM = """PROBLEM. A retailer manages one product with lost sales and a fixed integer lead time L.
The initial on-hand inventory and all outstanding orders are zero. An episode has L planning
periods with demand exactly zero, followed by 50 selling periods. Only selling-period costs
enter the objective. In EACH period, including planning periods, events occur in this order:
(1) Receive the order placed L periods earlier and add ALL of it to inventory.
(2) Observe on_hand_inventory AFTER that arrival and pipeline_orders, a list of length L-1.
    pipeline_orders[j] arrives in j+1 periods. Choose this period's new order q.
(3) Realize demand D, sell min(on_hand_inventory, D), and lose all unmet demand permanently.
(4) Carry remaining inventory forward; the new order q will arrive exactly L periods later.
(5) In selling periods, pay h times remaining inventory plus p times lost demand.
For example, at L=2 the policy sees one outstanding order arriving next period, and its NEW
order arrives two periods later. Do not count the current arrival twice.

Orders can be any NONNEGATIVE FINITE REAL number. There is no order capacity, inventory
capacity, ordering cost, backlog, or terminal salvage value. Inventory is never discarded.
The objective is MINIMUM EXPECTED TOTAL COST over the 50 selling periods, from the stated
initialization. Expectations average independent episodes of the given demand process.

The policy MUST BE STATIONARY: q is a function only of current on-hand inventory, current
pipeline, and fixed instance parameters. It has no period index, remaining horizon, phase
flag, demand history, or future demand. Do not use a counter, mutable global/closure state,
random seed state, or any other cross-call memory to infer the phase or episode position.
Precomputed FIXED constants or tables are allowed. Return a deterministic state-to-action
rule. The same rule is used in planning and selling periods.
"""

TOOLS = """TOOLS AND BUDGET. You have one tool, run_python(code). It executes Python with
the standard library, NumPy (importable as numpy) and SciPy. State does NOT persist between
calls: define everything you need in each call. Print the results you want to see. You have
3600 seconds of TOTAL Python execution across at most 50 calls, divided as you choose.
Remaining time is reported after every call. You may implement simulations, test, and revise
your approach within this budget. There is no web access, external data, repository access,
or external optimization solver. The final policy will be evaluated outside this session
on demand paths unavailable to you. Your final code must not call an LLM, network, files,
or subprocesses and may use only the standard library, NumPy and SciPy.

Final per-instance initialization should take at most 30 seconds on one CPU core. This is
a measured target; a separate 600-second guard stops a construction that never returns.
The per-period order function must be lightweight: no simulations or expensive optimization
on each policy call. You may precompute fixed tables and constants at initialization.
"""


def demand_definition(family: str, numeric_params=None) -> str:
    params = numeric_params or {}
    mean = params.get("mean_demand", "demand_mean")
    if family == "poisson":
        return f"Selling demands are i.i.d. Poisson with rate {mean}."
    if family == "exponential":
        return (
            f"For every selling demand draw X from Exponential(scale={mean}), then set D=np.rint(X). "
            "Thus demand is the nearest integer, NOT the continuous exponential draw. "
            "The scale is the mean of X, not its reciprocal."
        )
    if family == "normal":
        std = params.get("std_normal", "demand_std")
        return (
            f"For every selling demand draw X from Normal(loc={mean}, scale={std}), "
            "then set D=np.rint(max(0, X)). This is clipping negative draws to zero, "
            "NOT rejection sampling a truncated normal. The mean and standard deviation "
            "parameters describe X; clipping and rounding can change the moments of D."
        )
    raise ValueError(f"Unsupported family: {family}")


def make_prompt(level: str, family: str, params=None) -> str:
    if level == "L1":
        if params is None:
            raise ValueError("L1 requires numeric instance parameters")
        numbers = {k: params[k] for k in (
            "lead_time", "mean_demand", "holding_cost", "lost_sales_cost", "horizon"
        )}
        if family == "normal":
            numbers["std_normal"] = params["std_normal"]
        introduction = "Write an ordering policy for the following SPECIFIC problem.\n"
        instance = (
            "INSTANCE PARAMETERS (all known exactly):\n" + json.dumps(numbers, sort_keys=True)
            + "\nHere L=lead_time, h=holding_cost and p=lost_sales_cost.\n"
            + demand_definition(family, params)
        )
        contract = """FINAL OUTPUT. Return ONLY one Python code block defining:
def compute_order_amount(on_hand_inventory, pipeline_orders):
    ...
It must return a valid order for every nonnegative finite state with the stated shape.
Embed the given fixed parameters in your source. Include every helper and import needed.
Module-level initialization is permitted under the initialization-time target. Do not use
an OPT_PARAM wrapper or assume an external tuner will adjust your returned code."""
    elif level == "L2":
        introduction = "Write a general-purpose policy-design algorithm for the following CLASS of problems.\n"
        instance = (
            "PROBLEM CLASS. " + demand_definition(family)
            + "\nAll instance parameters are known exactly; nothing needs to be estimated. "
            "Future instances have integer lead_time in [2,10], demand_mean in [50,150], "
            "holding_cost=1, lost_sales_cost in [2,10], and horizon=50. "
            + ("For Normal, demand_std is in [10,100]. " if family == "normal" else "")
            + "No evaluation-instance list or example instances are supplied."
        )
        contract = """FINAL OUTPUT. Return ONLY one Python code block defining:
def design(params):
    ...
    return compute_order_amount
params is a dictionary with numeric keys lead_time, mean_demand, holding_cost,
lost_sales_cost, horizon, and (for the Normal class) std_normal. demand_mean in the
problem statement means params['mean_demand']; demand_std means params['std_normal'].
The returned callable has signature compute_order_amount(on_hand_inventory, pipeline_orders).
It must return a valid order for every nonnegative finite state with the stated shape.
design may perform instance-specific computation or simulation within the setup target;
it may not call an LLM or access external files. Include every helper and import needed.
The returned policy must be stationary and lightweight as specified above."""
    else:
        raise ValueError("level must be L1 or L2")
    return "\n\n".join((introduction, PROBLEM, instance, TOOLS, contract)) + "\n"


def session_specs():
    core = (
        ("poisson", "poisson_L6_c1_2"),
        ("normal", "normal_std30_L6_c1_2"),
        ("exponential", "exponential_L6_c1_2"),
    )
    # Interleave independent draws; no result-dependent ordering or prompt edits.
    for repeat in range(1, 4):
        for family, scenario_id in core:
            for level in ("L1", "L2"):
                yield {
                    "session_id": f"{level.lower()}_{family}_r{repeat}",
                    "level": level, "family": family, "repeat": repeat,
                    "scenario_id": scenario_id if level == "L1" else None,
                }
