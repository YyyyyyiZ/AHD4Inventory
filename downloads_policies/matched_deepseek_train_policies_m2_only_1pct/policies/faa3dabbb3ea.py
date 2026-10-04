# policy_hash: faa3dabbb3ea0ad7290f944477ebcfe38cd99bc1f91dba36b6b263e5d72c6c4e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 21
# source_prompt_files: 1
# best_target_performance: 1190.92
# best_prompt_performance: 1190.92
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_002202.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 288.4075534532081  # OPT_PARAM: {"initial": 288.4075534532081, "min": 250, "max": 320, "type": "float"}
    safety_stock = 18.512761940516235  # OPT_PARAM: {"initial": 18.512761940516235, "min": 10, "max": 30, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.9, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.6, "type": "float"}
    demand_adjustment = 0.09515001385491484  # OPT_PARAM: {"initial": 0.09515001385491484, "min": 0.0, "max": 0.1, "type": "float"}

    # Calculate effective inventory position
    weighted_pipeline = pipeline_weight * sum(pipeline_orders)
    effective_inventory = on_hand_inventory + weighted_pipeline

    # Base order calculation
    order_amount = max(0, base_stock - effective_inventory + safety_stock)

    # Apply demand-responsive adjustment
    if pipeline_orders and len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        if recent_order > 0:
            demand_signal = demand_adjustment * (recent_order - order_amount)
            order_amount += demand_signal

    # Apply smoothing
    if pipeline_orders and len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_order
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
