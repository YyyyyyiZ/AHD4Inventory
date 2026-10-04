# policy_hash: 16be11fd47f6221c348cd9333327caa625d4842ae602cdbf0a675c5ef153de5e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 4283.46
# best_prompt_performance: 4285.84
# best_rel_error_pct: 0.055563
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_230727.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 539.1260849726751  # OPT_PARAM: {"initial": 539.1260849726751, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 58.911969272773405  # OPT_PARAM: {"initial": 58.911969272773405, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.9, "type": "float"}
    lead_time = 6  # OPT_PARAM: {"initial": 6, "min": 1, "max": 10, "type": "int"}
    demand_multiplier = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline orders
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-min(lead_time, len(pipeline_orders)):]
        estimated_demand = sum(recent_orders) / len(recent_orders) * demand_multiplier
    else:
        estimated_demand = 0

    # Calculate expected shortfall with smoothing
    expected_shortfall = max(0, base_stock - inventory_position)

    # Add safety stock adjustment and demand forecast
    adjusted_shortfall = expected_shortfall + safety_stock + estimated_demand

    # Apply smoothing to avoid large order swings
    order_amount = max(0, smoothing_factor * adjusted_shortfall)

    # Round to nearest integer for practical ordering
    order_amount = int(round(order_amount))

    return order_amount
