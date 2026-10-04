# policy_hash: 1a17e941128d203a88508d25dcd9a8769ed31f0f19d164c23347e39e44ee8026
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1233.54
# best_prompt_performance: 1233.45
# best_rel_error_pct: 0.007296
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_012235.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 400.0  # OPT_PARAM: {"initial": 400.0, "min": 400, "max": 700, "type": "float"}
    safety_stock = 96.05974826406778  # OPT_PARAM: {"initial": 96.05974826406778, "min": 40, "max": 120, "type": "float"}
    demand_estimate = 115.78216793212297  # OPT_PARAM: {"initial": 115.78216793212297, "min": 80, "max": 120, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety stock
    expected_lead_time_demand = demand_estimate * lead_time
    target_position = expected_lead_time_demand + safety_stock

    # Calculate base order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply adjustment factor to smooth orders
    if order_amount > 0:
        order_amount = min(order_amount, base_stock * adjustment_factor)

    # Round to nearest integer since order amount should be integer
    return order_amount
