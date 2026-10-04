# policy_hash: 1843369c138480e3697a14e864711fb0c4126c880339da733c63e58155b600f9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 6207.88
# best_prompt_performance: 6207.88
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_080405.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 280.4998887642002  # OPT_PARAM: {"initial": 280.4998887642002, "min": 100, "max": 500, "type": "float"}
    safety_stock = 15.19988876420018  # OPT_PARAM: {"initial": 15.19988876420018, "min": 0, "max": 100, "type": "float"}
    smoothing_factor = 0.10670270749375631  # OPT_PARAM: {"initial": 0.10670270749375631, "min": 0.05, "max": 0.5, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline (weighted average emphasizing recent orders)
    if len(pipeline_orders) > 0:
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders), 0, -1)]
        weighted_pipeline = sum(w * q for w, q in zip(weights, pipeline_orders)) / sum(weights)
        pipeline_adjustment = 0.14954476866975547  # OPT_PARAM: {"initial": 0.14954476866975547, "min": 0.05, "max": 0.3, "type": "float"}
    else:
        pipeline_adjustment = 0

    # Dynamic target based on pipeline and safety stock
    dynamic_target = base_stock + safety_stock - pipeline_adjustment

    # Calculate raw order amount
    raw_order = max(0, dynamic_target - inventory_position)

    # Apply smoothing using recent pipeline orders
    if len(pipeline_orders) > 0:
        recent_avg = sum(pipeline_orders[-2:]) / min(2, len(pipeline_orders))
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * recent_avg
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
