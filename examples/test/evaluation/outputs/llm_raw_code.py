# --- OPTIMIZABLE PARAMETERS ---
base_stock_1 = 100.0  # OPT_PARAM: {'initial': 100.0, 'min': 50.0, 'max': 200.0, 'type': 'float'}
base_stock_2 = 100.0  # OPT_PARAM: {'initial': 100.0, 'min': 50.0, 'max': 200.0, 'type': 'float'}

# --- MAIN CODE ---
def llm_policy(state):
    t, I = state["t"], state["I"]
    if t == 1:
        return max(0.0, base_stock_1 - I)
    elif t == 2:
        return max(0.0, base_stock_2 - I)
    return 0.0