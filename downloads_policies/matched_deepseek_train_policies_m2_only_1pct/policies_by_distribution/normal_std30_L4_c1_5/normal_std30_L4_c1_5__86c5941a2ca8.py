# policy_hash: 86c5941a2ca81d0d30ceb376602e01881f93e6711ac9a48ee3662447c227fc6a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 3520.35
# best_prompt_performance: 3520.35
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_063618.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 453.2764650866602  # OPT_PARAM: {"initial": 453.2764650866602, "min": 350, "max": 550, "type": "float"}
    safety_stock = 38.27646508663749  # OPT_PARAM: {"initial": 38.27646508663749, "min": 20, "max": 80, "type": "float"}
    demand_multiplier = 0.7707620121470978  # OPT_PARAM: {"initial": 0.7707620121470978, "min": 0.6, "max": 1.1, "type": "float"}
    pipeline_weight = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.6, "type": "float"}
    max_order = 98.33366119135218  # OPT_PARAM: {"initial": 98.33366119135218, "min": 90, "max": 180, "type": "float"}
    min_order = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 40, "type": "float"}
    lead_time = 4  # OPT_PARAM: {"initial": 4, "min": 3, "max": 6, "type": "int"}
    smoothing_factor = 0.5231714009169403  # OPT_PARAM: {"initial": 0.5231714009169403, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent pipeline orders
    if len(pipeline_orders) >= 2:
        # Weight recent arrivals more heavily for better responsiveness
        recent_demand = (pipeline_orders[0] * 0.6 + pipeline_orders[1] * 0.4)
    elif pipeline_orders:
        recent_demand = pipeline_orders[0]
    else:
        recent_demand = 0

    # Adjust base stock based on recent demand pattern and pipeline status
    adjusted_base = base_stock + demand_multiplier * recent_demand

    # Incorporate pipeline information more directly
    pipeline_effect = pipeline_weight * sum(pipeline_orders[1:]) if len(pipeline_orders) > 1 else 0

    # Calculate order-up-to level with safety stock and pipeline adjustment
    order_up_to = adjusted_base + safety_stock - pipeline_effect

    # Calculate raw order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing with exponential smoothing
    if hasattr(compute_order_amount, 'prev_order'):
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * compute_order_amount.prev_order

    # Apply order bounds
    order_amount = min(max(order_amount, min_order), max_order)

    # Store for next smoothing
    compute_order_amount.prev_order = order_amount

    # Ensure integer order amount
    return order_amount
