# policy_hash: 65c2f28848922393b7ea36352e269225d194b15036c9baec143878bcb52cb6b4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1028.18
# best_prompt_performance: 1028.18
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_062519.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 290.6201599090864  # OPT_PARAM: {"initial": 290.6201599090864, "min": 250, "max": 350, "type": "float"}
    safety_stock = 5.0  # OPT_PARAM: {"initial": 5.0, "min": 5, "max": 15, "type": "float"}
    demand_smoothing = 0.45  # OPT_PARAM: {"initial": 0.45, "min": 0.3, "max": 0.7, "type": "float"}
    pipeline_weight = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    adjustment_factor = 0.34840705412658635  # OPT_PARAM: {"initial": 0.34840705412658635, "min": 0.2, "max": 0.6, "type": "float"}
    order_threshold = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent pipeline arrivals
    if len(pipeline_orders) >= 2:
        # Use weighted average of recent arrivals
        recent_estimate = pipeline_orders[0] * 0.7 + pipeline_orders[1] * 0.3
    else:
        recent_estimate = base_stock / 3.0

    # Smooth demand estimate
    smoothed_demand = demand_smoothing * recent_estimate + (1 - demand_smoothing) * (base_stock / 3.0)

    # Adjust base stock based on pipeline status
    pipeline_avg = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    pipeline_adjustment = pipeline_weight * (pipeline_avg - base_stock / 3.0)

    # Calculate target inventory position
    target_position = base_stock + safety_stock + adjustment_factor * pipeline_adjustment

    # Calculate order amount
    order_needed = target_position - inventory_position

    # Apply order threshold to avoid small orders
    if order_needed > order_threshold:
        order_amount = int(round(order_needed))
    else:
        order_amount = 0

    return order_amount
