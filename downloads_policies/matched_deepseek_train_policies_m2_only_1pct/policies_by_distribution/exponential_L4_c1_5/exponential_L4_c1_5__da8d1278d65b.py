# policy_hash: da8d1278d65b4aa643be1269b8e49d96dc6140c77f5311801a1d20d12c4ca413
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 11033.8
# best_prompt_performance: 11034.04
# best_rel_error_pct: 0.002175
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_045212.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 369.3598880972756  # OPT_PARAM: {"initial": 369.3598880972756, "min": 200, "max": 600, "type": "float"}
    demand_estimate = 104.91983684249087  # OPT_PARAM: {"initial": 104.91983684249087, "min": 80, "max": 200, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    buffer_multiplier = 0.7646394447872497  # OPT_PARAM: {"initial": 0.7646394447872497, "min": 0.5, "max": 1.5, "type": "float"}
    reorder_threshold = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.4, "max": 0.8, "type": "float"}
    min_order_multiplier = 1.2225018197833442  # OPT_PARAM: {"initial": 1.2225018197833442, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    # Base target plus buffer for demand variability during lead time
    target_position = base_stock + expected_lead_time_demand * buffer_multiplier

    # Calculate order needed to reach target
    order_needed = target_position - inventory_position

    # Apply smoothing and ensure non-negative order
    if order_needed > 0:
        # Smooth order adjustment
        order_amount = max(0, smoothing_factor * order_needed)

        # If inventory position is significantly below target, order more aggressively
        if inventory_position < target_position * reorder_threshold:
            order_amount = max(order_amount, demand_estimate * min_order_multiplier)
    else:
        order_amount = 0

    # Round to nearest integer (orders are discrete units)
    return order_amount
