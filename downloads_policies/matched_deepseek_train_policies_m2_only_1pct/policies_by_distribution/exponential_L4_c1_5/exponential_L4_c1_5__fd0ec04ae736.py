# policy_hash: fd0ec04ae736b255a1f4b88b2e47a1d72886be34bf80f734b495113fc0004513
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 11031.43
# best_prompt_performance: 11031.43
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_045029.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 442.66428341939525  # OPT_PARAM: {"initial": 442.66428341939525, "min": 300, "max": 700, "type": "float"}
    demand_estimate = 89.6999493709099  # OPT_PARAM: {"initial": 89.6999493709099, "min": 80, "max": 200, "type": "float"}
    smoothing_factor = 0.31394160245702735  # OPT_PARAM: {"initial": 0.31394160245702735, "min": 0.2, "max": 0.8, "type": "float"}
    buffer_multiplier = 0.5923512993866675  # OPT_PARAM: {"initial": 0.5923512993866675, "min": 0.2, "max": 1.0, "type": "float"}
    reorder_threshold = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}

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
            order_amount = max(order_amount, demand_estimate * 1.5)
    else:
        order_amount = 0

    # Round to nearest integer (orders are discrete units)
    return order_amount
