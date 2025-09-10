# toy_pipeline_2p_llm_fixed.py
import os, re, ast, json, textwrap, requests
from typing import Dict, List, Tuple
import numpy as np

# === Your optimizer ===
from eoh.methods.eoh.external_scipy import ScipyOptimizer

# === Interface evaluator: execute code and read required metrics for optimizer ===
class OptimizerInterfaceEval:
    def __init__(self):
        self.prompts = {}

    def evaluate(self, code_str: str):
        ns = {"__name__": "__main__"}  # Optional: give a module name
        exec(code_str, ns, ns)         # ★ Key: globals=ns, locals=ns

        avg = float(ns["avg"])
        test_obj = float(ns["test_obj"])
        lower = float(ns["lower"])
        upper = float(ns["upper"])
        trajectory = list(ns["trajectory"])
        cost_matrix = ns.get("cost_matrix", np.array([[avg, test_obj], [lower, upper]], dtype=float))
        order_matrix = ns.get("order_matrix", np.zeros((1, 1), dtype=float))
        return {
            "avg": avg,
            "test_obj": test_obj,
            "lower": lower,
            "upper": upper,
            "trajectory": trajectory,
            "cost_matrix": cost_matrix,
            "order_matrix": order_matrix,
        }

# === Clean up LLM output wrapped in ``` ===
def clean_code_string(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
    s = re.sub(r"```$", "", s)
    return s.strip()

# === Parse optimizable parameter definitions at the top of LLM code (format: param = value  # OPT_PARAM: {...}) ===
OPT_PARAM_RE = re.compile(
    r"""^([A-Za-z_]\w*)\s*=\s*([^\n#]+?)\s*#\s*OPT_PARAM:\s*(\{.*\})\s*$"""
)

def parse_opt_params_from_code(llm_code: str) -> Tuple[Dict[str, Dict], List[str]]:
    """
    Read all lines like:
      X = 10  # OPT_PARAM: {'initial': 10, 'min': 0, 'max': 100, 'type': 'float'}
    and construct opt_params and param_vars.
    """
    opt_params: Dict[str, Dict] = {}
    param_vars: List[str] = []

    for line in llm_code.splitlines():
        m = OPT_PARAM_RE.match(line.strip())
        if not m:
            continue
        name, value_expr, meta_str = m.groups()
        try:
            meta = ast.literal_eval(meta_str)
        except Exception as e:
            raise ValueError(f"Failed to parse OPT_PARAM for {name}: {meta_str}") from e

        ptype = str(meta.get("type", "float")).lower()
        if ptype not in ("int","float"):
            raise ValueError(f"Unsupported type for {name}: {ptype}")
        init = meta.get("initial")
        pmin = meta.get("min")
        pmax = meta.get("max")
        if init is None or pmin is None or pmax is None:
            raise ValueError(f"Missing initial/min/max in OPT_PARAM for {name}")

        opt_params[name] = {
            "initial": init,
            "min": pmin,
            "max": pmax,
            "type": ptype
        }
        param_vars.append(name)

    if not param_vars:
        raise ValueError("No optimizable parameters found. Ensure lines like: x = 1  # OPT_PARAM: {...}")
    return opt_params, param_vars

# === Embed LLM code into “optimizer-executable” evaluation scaffold ===
def make_optimizer_ready_code(llm_code: str) -> str:

    scaffold = f"""
# === LLM CODE (Parameters + llm_policy(state)) ===
{llm_code}

# === EVALUATION SCAFFOLD (2-period, lost-sales, immediate arrival; float quantities) ===
import json, numpy as np

def simulate_episode_2p(policy_fn, d1, d2, h, p):
    I = 0.0  # use float inventory
    # t=1 ——— NO rounding, continuous q
    q1 = max(0.0, float(policy_fn({{"t":1,"I":I}})))
    inv1 = I + q1
    sales1 = min(inv1, float(d1))
    I = inv1 - sales1
    lost1 = float(d1) - sales1
    cost1 = h * I + p * lost1

    # t=2
    q2 = max(0.0, float(policy_fn({{"t":2,"I":I}})))
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
"""
    return scaffold

# === Construct fixed-format prompt and call LLM ===
FIXED_PARAM_GUIDE = """
When providing code, follow these requirements for optimizable parameters:
1) DECLARE ALL OPTIMIZABLE PARAMETERS AT THE BEGINNING:
   - Group all optimizable parameters in a dedicated section at the start
   - Each declaration must use this format:
     param_name = initial_value  # OPT_PARAM: {'initial': 50, 'min': 10, 'max': 200, 'type': 'float'}

2) PARAMETER USAGE IN CODE:
   - After declaration section, only reference parameters by name
   - Never use hard-coded numeric values that should be parameters
   - Example correct usage:
     order_quantity = base_stock * 2  # NOT: order_quantity = 100

3) REQUIREMENTS:
   - All optimizable parameters must be continuous variables (floats)
   - Include these attributes for each parameter:
     * initial: Starting value
     * min: Minimum allowed value
     * max: Maximum allowed value
     * type: Data type ('float')
   - No function parameters may be marked as optimizable. Only mark parameters assigned within the code body.

Example structure:
# --- OPTIMIZABLE PARAMETERS ---
base_stock = 50.0  # OPT_PARAM: {'initial': 50.0, 'min': 10.0, 'max': 200.0, 'type': 'float'}
reorder_point = 30.0  # OPT_PARAM: {'initial': 30.0, 'min': 5.0, 'max': 150.0, 'type': 'float'}

# --- MAIN CODE ---
def llm_policy(state):
    t, I = state["t"], state["I"]
    # Use base_stock and reorder_point above; avoid new hard-coded constants
    if I < reorder_point:
        return max(0.0, base_stock - I)  # return float
    return 0.0

DON'T mark any optimizable parameters in the main code.
"""

def prompt_llm_for_code(train_json_path: str) -> str:

    with open(train_json_path, "r") as f:
        train_json = json.load(f)

    # Take a few samples to help calibrate (not required)
    samples = "\n".join(
        f"Sample {i+1}: d1={ep['d'][0]}, d2={ep['d'][1]}"
        for i, ep in enumerate(train_json["data"][:50])
    )
    h = train_json["meta"]["cost_params"]["h"]
    p = train_json["meta"]["cost_params"]["p"]

    system_prompt = "You are an expert in 2-period lost-sales newsvendor with immediate arrivals (no lead time)."
    user_prompt = f"""
We optimize a 2-period lost-sales newsvendor. Each period:
- Decision q_t >= 0 arrives immediately (no lead time).
- State for decision uses only current period info: state = {{"t": 1 or 2, "I": current on-hand at start}}.
- Cost per period: holding h*ending_inventory + penalty p*lost_sales. Here h={h}, p={p}.
- Training/validation share the same i.i.d. demand distribution.

Write ONLY Python code (no explanations) that satisfies:
- Put ALL optimizable parameters at the top using the exact format with # OPT_PARAM: {{...}}
- Then define exactly: def llm_policy(state):
- llm_policy must return a nonnegative float order quantity (real-valued).
- Do not read files, do not use future demand.

{FIXED_PARAM_GUIDE}

A few training samples:
{samples}
"""
    api_key = os.getenv("DEEPSEEK_API_KEY") or "sk-5d290dc8a98e43c99f0e5d09ffb40d72"
    url = "https://api.deepseek.com/chat/completions"
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    resp.raise_for_status()
    print(resp.json()["choices"][0]["message"]["content"])
    c = input()
    code = clean_code_string(resp.json()["choices"][0]["message"]["content"])
    return code

# === Convenience: offline placeholder policy (can run without LLM) ===
OFFLINE_DEMO_CODE = textwrap.dedent("""
# --- OPTIMIZABLE PARAMETERS ---
base_stock_1 = 22.0  # OPT_PARAM: {'initial': 22.0, 'min': 0.0, 'max': 120.0, 'type': 'float'}
base_stock_2 = 20.0  # OPT_PARAM: {'initial': 20.0, 'min': 0.0, 'max': 120.0, 'type': 'float'}
reorder_point = 10.0  # OPT_PARAM: {'initial': 10.0, 'min': 0.0, 'max': 120.0, 'type': 'float'}

# --- MAIN CODE ---
def llm_policy(state):
    t, I = state["t"], state["I"]
    U = base_stock_1 if t == 1 else base_stock_2
    if I < reorder_point:
        return max(0.0, U - I)  # return float
    return max(0.0, U - I)      # return float
""")

# === Main process ===
if __name__ == "__main__":
    # 1) Ensure data exists
    train_path = "./evaluation/data/poisson1_train_80_low.json"
    val_path   = "./evaluation/data/poisson1_test_80_low.json"
    assert os.path.exists(train_path) and os.path.exists(val_path), \
        "Please run gen_data_2p_newsvendor.py first."

    # 2) Get LLM code (switchable to offline placeholder)
    use_offline = False 
    if use_offline:
        llm_code = OFFLINE_DEMO_CODE
    else:
        llm_code = prompt_llm_for_code(train_path)

    # 3) Parse LLM top-level optimizable parameters
    opt_params, param_vars = parse_opt_params_from_code(llm_code)
    print("Parsed opt params:", opt_params)

    # 4) Assemble into complete code “ready for optimizer execution”
    opt_ready_code = make_optimizer_ready_code(llm_code)
    
    # 5) Optimization
    iface = OptimizerInterfaceEval()
    optimizer = ScipyOptimizer(interface_eval=iface, max_iter=50, timeout=10.0)
    result = optimizer.optimize(
        original_code=opt_ready_code,
        opt_params=opt_params,
        param_vars=param_vars
    )

    print("\n=== Optimization Result ===")
    print("Success:", result.success)
    print("Optimized params:", result.optimized_params)
    print("Train avg (objective):", result.optimized_fitness)
    print("Val (test_obj):", result.optimized_test_fitness)

    # 6) Optional: save raw LLM code and optimized full code
    os.makedirs("./evaluation/outputs", exist_ok=True)
    with open("./evaluation/outputs/llm_raw_code.py", "w") as f:
        f.write(llm_code)
    with open("./evaluation/outputs/llm_optimized_fullcode.py", "w") as f:
        f.write(result.optimized_code)
    print("Saved ./evaluation/outputs/llm_raw_code.py and llm_optimized_fullcode.py")
