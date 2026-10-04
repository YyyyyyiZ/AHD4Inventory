# policy_hash: e5366d4b3774e91de989ea564c3a175df290e133902637c3bd1d7e64209b799c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 2
# best_target_performance: 6113.14
# best_prompt_performance: 6113.14
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_093713.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 381.4054652051868  # OPT_PARAM: {"initial": 381.4054652051868, "min": 200, "max": 600, "type": "float"}
    pipeline_weight = 0.6593233321146832  # OPT_PARAM: {"initial": 0.6593233321146832, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.15501138344547383  # OPT_PARAM: {"initial": 0.15501138344547383, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock = 81.40546520518718  # OPT_PARAM: {"initial": 81.40546520518718, "min": 30, "max": 150, "type": "float"}
    demand_buffer = 1.4003575453402775  # OPT_PARAM: {"initial": 1.4003575453402775, "min": 0.8, "max": 1.5, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply demand-based adjustment
    if raw_order > 0:
        # Use weighted average of recent pipeline as demand indicator
        recent_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.3, "max": 0.9, "type": "float"}
        if len(pipeline_orders) >= 3:
            recent_arrivals = (pipeline_orders[0] * 0.5 +
                             pipeline_orders[1] * 0.3 +
                             pipeline_orders[2] * 0.2) * recent_weight
        else:
            recent_arrivals = sum(pipeline_orders) * 0.5 * recent_weight

        if recent_arrivals > 0:
            demand_adjusted = raw_order * demand_buffer
            raw_order = min(demand_adjusted, raw_order * 1.5)

    # Apply smoothing with minimum order threshold
    min_order_threshold = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 10, "max": 50, "type": "float"}
    if raw_order > min_order_threshold:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
