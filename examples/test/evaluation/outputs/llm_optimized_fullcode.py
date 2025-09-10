
# === LLM CODE (Parameters + llm_policy(state)) ===
# --- OPTIMIZABLE PARAMETERS ---
base_stock_1 = 86.99999999366547  # Optimized
base_stock_2 = 90.00000680202696  # Optimized

# --- MAIN CODE ---
def llm_policy(state):
    t, I = state["t"], state["I"]
    if t == 1:
        return max(0.0, base_stock_1 - I)
    elif t == 2:
        return max(0.0, base_stock_2 - I)
    return 0.0

# === EVALUATION SCAFFOLD (2-period, lost-sales, immediate arrival; float quantities) ===
import json, numpy as np

def simulate_episode_2p(policy_fn, d1, d2, h, p):
    I = 0.0  # use float inventory
    # t=1 ——— NO rounding, continuous q
    q1 = max(0.0, float(policy_fn({"t":1,"I":I})))
    inv1 = I + q1
    sales1 = min(inv1, float(d1))
    I = inv1 - sales1
    lost1 = float(d1) - sales1
    cost1 = h * I + p * lost1

    # t=2
    q2 = max(0.0, float(policy_fn({"t":2,"I":I})))
    inv2 = I + q2
    sales2 = min(inv2, float(d2))
    I = inv2 - sales2
    lost2 = float(d2) - sales2
    cost2 = h * I + p * lost2

    return cost1 + cost2

def eval_dataset(path):
    with open(path, "r") as f:
        data = json.load(f)
    h = float(data["meta"]["cost_params"]["h"])
    p = float(data["meta"]["cost_params"]["p"])
    costs = []
    for ep in data["data"]:
        d1, d2 = ep["d"]
        c = simulate_episode_2p(llm_policy, d1, d2, h, p)
        costs.append(c)
    return float(np.mean(costs))

avg = eval_dataset("./evaluation/data/poisson1_train_80_low.json")
test_obj = eval_dataset("./evaluation/data/poisson1_test_80_low.json")  # use validation set
lower = avg - 0.1
upper = avg + 0.1
trajectory = [avg, test_obj]
cost_matrix = np.array([[avg, test_obj],[lower, upper]], dtype=float)
order_matrix = np.zeros((1,1), dtype=float)
