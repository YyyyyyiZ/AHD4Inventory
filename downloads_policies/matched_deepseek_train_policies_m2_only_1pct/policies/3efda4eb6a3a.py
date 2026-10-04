# policy_hash: 3efda4eb6a3aaae9bf3ba7c2c83a085be9b7ae3ad44b34934436c0fe1aaafb11
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 34
# source_prompt_files: 1
# best_target_performance: 6226.94
# best_prompt_performance: 6226.94
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_032050.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 850.0  # OPT_PARAM: {"initial": 850.0, "min": 500, "max": 1200, "type": "float"}
    safety_stock = 161.12269727972014  # OPT_PARAM: {"initial": 161.12269727972014, "min": 50, "max": 300, "type": "float"}
    demand_estimate = 84.32868126595304  # OPT_PARAM: {"initial": 84.32868126595304, "min": 80, "max": 130, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time plus review period
    expected_demand_during_leadtime = demand_estimate * (lead_time + 1)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    max_order_multiplier = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.5, "max": 4.0, "type": "float"}

    # Smooth the order amount
    order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Cap order amount reasonably
    max_order = max_order_multiplier * demand_estimate
    order_amount = min(order_amount, max_order)

    # Round to nearest integer (orders must be integer quantities)
    order_amount = int(round(order_amount))

    return order_amount
