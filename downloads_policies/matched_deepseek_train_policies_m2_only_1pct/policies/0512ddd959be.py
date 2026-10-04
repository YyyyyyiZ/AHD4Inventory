# policy_hash: 0512ddd959bedb347c61734f97212854d69c90d8fb4672bde856dce9a702aa55
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 36
# source_prompt_files: 1
# best_target_performance: 3523.43
# best_prompt_performance: 3523.43
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_062913.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 430.79880747980457  # OPT_PARAM: {"initial": 430.79880747980457, "min": 300, "max": 600, "type": "float"}
    safety_stock = 42.19160121291591  # OPT_PARAM: {"initial": 42.19160121291591, "min": 30, "max": 100, "type": "float"}
    demand_multiplier = 0.6607092689813702  # OPT_PARAM: {"initial": 0.6607092689813702, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.5, "type": "float"}
    max_order = 97.65123669800143  # OPT_PARAM: {"initial": 97.65123669800143, "min": 80, "max": 200, "type": "float"}
    min_order = 19.873783390261227  # OPT_PARAM: {"initial": 19.873783390261227, "min": 10, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using simple average of recent pipeline orders
    if len(pipeline_orders) >= 2:
        # Use average of two most recent arrivals for better stability
        recent_demand = (pipeline_orders[0] + pipeline_orders[1]) / 2
    elif pipeline_orders:
        recent_demand = pipeline_orders[0]
    else:
        recent_demand = 0

    # Adjust base stock based on recent demand pattern
    adjusted_base = base_stock + demand_multiplier * recent_demand

    # Calculate order-up-to level with safety stock
    order_up_to = adjusted_base + safety_stock

    # Calculate raw order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply order smoothing with bounds
    order_amount = min(max(order_amount, min_order), max_order)

    # Ensure integer order amount
    return order_amount
