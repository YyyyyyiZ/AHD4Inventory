# policy_hash: fe33d8df415b1a0a33b9bd9e20a007b9028c4329152bbe853231c6ac2f69f10a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1420.06
# best_prompt_performance: 1409.81
# best_rel_error_pct: 0.721800
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_020508.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 920.0  # OPT_PARAM: {"initial": 920.0, "min": 800, "max": 1100, "type": "float"}
    demand_estimate = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 95, "max": 105, "type": "float"}
    safety_factor = 1.3  # OPT_PARAM: {"initial": 1.3, "min": 1.3, "max": 1.8, "type": "float"}
    max_order_cap = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 200, "type": "float"}
    min_order_cap = 19.95515021076937  # OPT_PARAM: {"initial": 19.95515021076937, "min": 10, "max": 30, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety factor
    expected_lead_time_demand = demand_estimate * lead_time
    safety_stock = safety_factor * demand_estimate * (lead_time ** 0.5)

    # Calculate target inventory position
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate base order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply order caps
    order_amount = min(order_amount, max_order_cap)

    # Apply minimum order threshold
    if order_amount > 0 and order_amount < min_order_cap:
        order_amount = min_order_cap

    # Ensure integer output
    return order_amount
