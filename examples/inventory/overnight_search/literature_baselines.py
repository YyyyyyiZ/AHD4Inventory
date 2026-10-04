"""BSP-low-EW literature formula, adapted to the stated mixed-issuance model.

Formula source: De Moor, Gijsbrechts & Boute (2022), author manuscript p.7,
https://ciencia.ucp.pt/ws/portalfiles/portal/91570599/39282916.pdf
The paper attributes the policy to Haijema & Minner (2019).

The source defines estimated waste by deterministic mean demand over lead time.
Here FIFO and LIFO means are served in our model's order. This mixed-issuance
adaptation is explicit; neither PIL/APIL nor their theoretical guarantees are
claimed. The code supplier supports precisely L=2, the screening grid.
"""
from __future__ import annotations

import numpy as np


def bsp_low_ew_code() -> str:
    """An AST-validator-compatible three-parameter policy for L=2."""
    return '''def compute_order_amount(age, pipeline, mu, cv, f, L):
    S1 = 8.0 # OPT_PARAM: {"type":"float","initial":8.0,"min":0.0,"max":60.0}
    S2 = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    b = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.25,"max":60.0}
    onhand = sum(age)
    ip = onhand + sum(pipeline)
    fifo = f*mu
    after_demand = max(0.0,onhand-mu)
    waste0 = min(max(0.0,age[0]-fifo),after_demand)
    next_oldest = min(max(0.0,age[0]+age[1]-fifo),after_demand)-waste0
    next_onhand = after_demand-waste0+pipeline[0]
    waste1 = min(max(0.0,next_oldest-fifo),max(0.0,next_onhand-mu))
    ew = waste0+waste1
    alpha = 1.0-(S2-S1)/b
    if ip < b:
        return max(0.0,S1-alpha*ip+ew)
    return max(0.0,S2-ip+ew)
'''


def policy_codes() -> dict[str, str]:
    return {"bsp_low_ew_mixed_l2": bsp_low_ew_code()}


def estimated_waste_l2(age, pipeline, mu, f):
    """Analytic deterministic two-period waste with receipt between periods."""
    onhand = float(np.sum(age))
    remaining = max(0.0, onhand - mu)
    waste0 = min(max(0.0, age[0] - f * mu), remaining)
    next_oldest = min(max(0.0, age[0] + age[1] - f * mu), remaining) - waste0
    next_onhand = remaining - waste0 + pipeline[0]
    waste1 = min(max(0.0, next_oldest - f * mu), max(0.0, next_onhand - mu))
    return waste0 + waste1


def verify() -> dict:
    """Compare closed form to an independently written fluid-stock recursion."""
    rng = np.random.default_rng(498130)
    cases = 0
    maximum_error = 0.0
    for m in (3, 4, 5):
        for f in (0.0, 0.25, 0.5, 1.0):
            for _ in range(200):
                original = rng.uniform(0, 12, size=m)
                pipeline = rng.uniform(0, 12, size=1)
                mu = float(rng.uniform(0.25, 9))
                predicted = estimated_waste_l2(original, pipeline, mu, f)
                age = original.copy()
                reference = 0.0
                for t in range(2):
                    fifo, lifo = f * mu, (1 - f) * mu
                    for j in range(m):
                        sold = min(age[j], fifo)
                        age[j] -= sold
                        fifo -= sold
                    for j in range(m - 1, -1, -1):
                        sold = min(age[j], lifo)
                        age[j] -= sold
                        lifo -= sold
                    reference += age[0]
                    age[:-1] = age[1:]
                    age[-1] = pipeline[0] if t == 0 else 0.0
                maximum_error = max(maximum_error, abs(predicted - reference))
                assert abs(predicted - reference) < 1e-10
                cases += 1
    # Supply the exact six-argument AST grammar expected by the common worker.
    from ..correlated_benchmark import fast_policy
    original_arguments = fast_policy.ARGUMENTS
    try:
        fast_policy.ARGUMENTS = ("age", "pipeline", "mu", "cv", "f", "L")
        prepared = fast_policy.prepare_policy(bsp_low_ew_code(), None)
        assert len(prepared["opt_params"]) == 3
    finally:
        fast_policy.ARGUMENTS = original_arguments
    return {"fluid_recursion_cases": cases, "max_error": maximum_error,
            "parameter_count": 3, "validated_numerical_subset": True}


if __name__ == "__main__":
    import json
    print(json.dumps(verify(), indent=2))
