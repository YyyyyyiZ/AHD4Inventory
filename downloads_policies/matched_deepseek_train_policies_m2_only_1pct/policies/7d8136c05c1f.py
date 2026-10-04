# policy_hash: 7d8136c05c1fe23da0e9fa7ac21584131f14a335b85883de099caa3e1272275d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 6105.38
# best_prompt_performance: 6105.38
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_094016.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 384.13003616468575  # OPT_PARAM: {"initial": 384.13003616468575, "min": 300, "max": 500, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.4, "type": "float"}
    safety_stock = 123.63003616468677  # OPT_PARAM: {"initial": 123.63003616468677, "min": 80, "max": 180, "type": "float"}
    demand_buffer = 1.3  # OPT_PARAM: {"initial": 1.3, "min": 1.0, "max": 1.3, "type": "float"}
    min_order_threshold = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 5, "max": 20, "type": "float"}
    pipeline_lookback = 2  # OPT_PARAM: {"initial": 2, "min": 1, "max": 4, "type": "int"}
    recent_demand_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply demand-based adjustment using recent pipeline arrivals
    if raw_order > 0 and len(pipeline_orders) > 0:
        # Look at recent pipeline arrivals as proxy for recent demand
        recent_arrivals = sum(pipeline_orders[:pipeline_lookback]) / pipeline_lookback if pipeline_lookback > 0 else 0
        if recent_arrivals > 0:
            # Blend between base order and demand-adjusted order
            demand_adjusted = raw_order * demand_buffer
            blended_order = raw_order * (1 - recent_demand_weight) + demand_adjusted * recent_demand_weight
            raw_order = min(blended_order, raw_order * 1.2)

    # Apply smoothing with minimum order threshold
    if raw_order > min_order_threshold:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
