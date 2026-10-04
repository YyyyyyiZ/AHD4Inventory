# policy_hash: 52656d890581258d03e45c70add89b810b7868c929374cdc096708b759050cf9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 6100.66
# best_prompt_performance: 6100.66
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_094745.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 453.42051811682586  # OPT_PARAM: {"initial": 453.42051811682586, "min": 350, "max": 550, "type": "float"}
    pipeline_weight = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.85, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.4, "type": "float"}
    safety_stock = 78.42051811682684  # OPT_PARAM: {"initial": 78.42051811682684, "min": 50, "max": 120, "type": "float"}
    demand_buffer = 1.3  # OPT_PARAM: {"initial": 1.3, "min": 1.0, "max": 1.3, "type": "float"}
    min_order_threshold = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 5, "max": 25, "type": "float"}
    recent_demand_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.3, "max": 0.8, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply demand-based adjustment using recent arrivals
    if raw_order > 0 and len(pipeline_orders) >= 2:
        # Weight recent arrivals more heavily for demand signal
        recent_arrivals = (pipeline_orders[0] * (1 - recent_demand_weight) +
                          pipeline_orders[1] * recent_demand_weight)
        if recent_arrivals > 0:
            demand_adjusted = raw_order * demand_buffer
            # Cap the adjustment to avoid over-ordering
            raw_order = min(demand_adjusted, raw_order * 1.2)

    # Apply smoothing with minimum order threshold
    if raw_order > min_order_threshold:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
