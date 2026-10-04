# policy_hash: a361996a8fbde787430f9077b31de35c1fedf75582d8eb860de5e8fcb631063a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 6044.24
# best_prompt_performance: 6044.24
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_094207.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 449.3538302419643  # OPT_PARAM: {"initial": 449.3538302419643, "min": 300, "max": 600, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.15  # OPT_PARAM: {"initial": 0.15, "min": 0.15, "max": 0.4, "type": "float"}
    safety_stock = 99.35383024196422  # OPT_PARAM: {"initial": 99.35383024196422, "min": 50, "max": 150, "type": "float"}
    demand_buffer = 1.2820920077207547  # OPT_PARAM: {"initial": 1.2820920077207547, "min": 1.0, "max": 1.5, "type": "float"}
    min_order_threshold = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 30, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply demand-based adjustment
    if raw_order > 0:
        # Use simple average of recent pipeline as demand indicator
        if len(pipeline_orders) >= 2:
            recent_arrivals = (pipeline_orders[0] + pipeline_orders[1]) / 2.0
        else:
            recent_arrivals = pipeline_orders[0] if pipeline_orders else 0

        if recent_arrivals > 0:
            demand_adjusted = raw_order * demand_buffer
            raw_order = min(demand_adjusted, raw_order * 1.3)

    # Apply smoothing with minimum order threshold
    if raw_order > min_order_threshold:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
