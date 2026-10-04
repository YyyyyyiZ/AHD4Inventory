# policy_hash: bdb9750ed240a4949bbdbf592fdc31f9718272e11c2efcd4cef502310a4fb458
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 1193.9
# best_prompt_performance: 1193.9
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_001441.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 293.0232869895717  # OPT_PARAM: {"initial": 293.0232869895717, "min": 280, "max": 350, "type": "float"}
    safety_stock = 6.823355441486112  # OPT_PARAM: {"initial": 6.823355441486112, "min": 5, "max": 25, "type": "float"}
    pipeline_weight = 0.9313857449952145  # OPT_PARAM: {"initial": 0.9313857449952145, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.31450177467786505  # OPT_PARAM: {"initial": 0.31450177467786505, "min": 0.2, "max": 0.8, "type": "float"}
    demand_adjustment = 0.19283404063876292  # OPT_PARAM: {"initial": 0.19283404063876292, "min": 0.0, "max": 0.3, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    weighted_pipeline = pipeline_weight * sum(pipeline_orders)
    effective_inventory = on_hand_inventory + weighted_pipeline

    # Base order calculation with safety stock
    order_amount = max(0, base_stock - effective_inventory + safety_stock)

    # Apply demand-responsive adjustment based on recent pipeline activity
    if pipeline_orders and len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        # Adjust order based on recent ordering pattern
        if recent_order > 0:
            demand_signal = demand_adjustment * (recent_order - order_amount)
            order_amount += demand_signal

    # Apply smoothing using most recent order if available
    if pipeline_orders and len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_order
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
