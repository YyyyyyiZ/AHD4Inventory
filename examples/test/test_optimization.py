# test_optimizer.py
import numpy as np
from eoh.methods.eoh.external_scipy import ScipyOptimizer

class DummyInterfaceEval:
    def evaluate(self, code_str: str):
        local_ns = {}
        exec(code_str, {}, local_ns)

        # Required fields (optimizer will at least use these)
        avg = float(local_ns["avg"])
        test_obj = float(local_ns["test_obj"])
        lower = float(local_ns["lower"])
        upper = float(local_ns["upper"])
        trajectory = list(local_ns["trajectory"])

        # —— Optional fields: provide safe defaults (external optimizer/logger may access them) ——
        # If your real environment needs them, you can also compute them in code_str and put into local_ns.
        cost_matrix = np.array([[avg, test_obj],
                                [lower, upper]], dtype=float)

        # Provide a reasonable size, safe value default order_matrix
        # For example, set the "order/decision" matrix as a 1x1 zero matrix
        order_matrix = np.zeros((1, 1), dtype=float)

        # You may also provide other optional keys if needed by your project
        policy = None
        extra_info = {}

        return {
            "avg": avg,
            "test_obj": test_obj,
            "lower": lower,
            "upper": upper,
            "trajectory": trajectory,
            "cost_matrix": cost_matrix,     # ★ Added
            "order_matrix": order_matrix,   # ★ Added
            "policy": policy,               # Optional
            "extra": extra_info,            # Optional
        }

# 2) Code to be optimized (must have top-level param = value)
original_code = """
alpha = 0.5
beta = 1.0

def score(a, b):
    return (a - 1.5)**2 + (b - 2.0)**2

train_score = score(alpha, beta)
test_score = score(alpha, beta)

avg = train_score
test_obj = test_score
lower = avg - 0.1
upper = avg + 0.1
trajectory = [avg, test_obj]
"""

# 3) Parameter configuration
opt_params = {
    "alpha": {"initial": 0.5, "min": -5, "max": 5, "type": "float"},
    "beta":  {"initial": 1.0, "min": -5, "max": 5, "type": "float"},
}
param_vars = ["alpha", "beta"]

# 4) Call optimizer
optimizer = ScipyOptimizer(interface_eval=DummyInterfaceEval(), max_iter=50, timeout=5.0)
result = optimizer.optimize(original_code, opt_params, param_vars)

print("Optimization success:", result.success)
print("Optimal parameters:", result.optimized_params)
print("Optimal objective value:", result.optimized_fitness)
print("Optimized code:\n", result.optimized_code)
