# policy_hash: f455f29e0aa05fd8f2d48192f881e587f6082abf7c44186e1c3d4d779be65743
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 6167.12
# best_prompt_performance: 6167.12
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_033250.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 780.0  # OPT_PARAM: {"initial": 780.0, "min": 500, "max": 1200, "type": "float"}
    safety_stock = 126.50635078056735  # OPT_PARAM: {"initial": 126.50635078056735, "min": 50, "max": 300, "type": "float"}
    demand_estimate = 89.60057425619387  # OPT_PARAM: {"initial": 89.60057425619387, "min": 80, "max": 130, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time plus review period
    expected_demand_during_leadtime = demand_estimate * (lead_time + 1)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate base order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply more aggressive smoothing
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    max_order_multiplier = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.5, "max": 4.0, "type": "float"}

    # Smooth the order amount more heavily
    order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Cap order amount more conservatively
    max_order = max_order_multiplier * demand_estimate
    order_amount = min(order_amount, max_order)

    # Add dynamic adjustment based on pipeline variability
    if len(pipeline_orders) > 1:
        pipeline_std = (max(pipeline_orders) - min(pipeline_orders)) / 2.0
        if pipeline_std > demand_estimate * 0.3:
            order_amount = order_amount * 0.8  # Reduce orders if pipeline is volatile

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
