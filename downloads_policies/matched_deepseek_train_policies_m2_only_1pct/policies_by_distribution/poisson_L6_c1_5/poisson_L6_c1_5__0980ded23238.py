# policy_hash: 0980ded2323861dd7586f05fdb5d5494cd76ddcef33657e9d32d6a411bb96eae
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 44
# source_prompt_files: 1
# best_target_performance: 1177.6
# best_prompt_performance: 1177.56
# best_rel_error_pct: 0.003397
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_015649.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 780.0  # OPT_PARAM: {"initial": 780.0, "min": 600, "max": 900, "type": "float"}
    demand_estimate = 117.5913738113381  # OPT_PARAM: {"initial": 117.5913738113381, "min": 80, "max": 120, "type": "float"}
    safety_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.5, "type": "float"}
    max_order_cap = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 200, "type": "float"}
    min_order_cap = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 10, "max": 50, "type": "float"}
    demand_smoothing = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety factor
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)
    safety_stock = safety_factor * demand_estimate

    # Calculate target inventory position
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate base order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply demand smoothing to reduce order volatility
    order_amount = demand_smoothing * order_amount + (1 - demand_smoothing) * demand_estimate

    # Apply order caps
    order_amount = min(order_amount, max_order_cap)

    # Apply minimum order threshold
    if order_amount > 0 and order_amount < min_order_cap:
        order_amount = min_order_cap

    # Ensure integer output
    return order_amount
