# policy_hash: 3cecaf765fa739c6c5607dc70a2238e0ffbb047e2414dea4df8b6c332b9f4825
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 2068.04
# best_prompt_performance: 2068.06
# best_rel_error_pct: 0.000967
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_054726.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 594.6052157157833  # OPT_PARAM: {"initial": 594.6052157157833, "min": 400, "max": 700, "type": "float"}
    safety_stock = 164.7052157157958  # OPT_PARAM: {"initial": 164.7052157157958, "min": 80, "max": 180, "type": "float"}
    smoothing_factor = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}
    demand_buffer = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.4, "type": "float"}
    pipeline_weight = 0.3315099776303392  # OPT_PARAM: {"initial": 0.3315099776303392, "min": 0.1, "max": 0.5, "type": "float"}
    min_order = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 20, "max": 100, "type": "float"}
    max_order = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 150, "max": 300, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand using weighted pipeline average
    weighted_sum = 0.0
    weight_sum = 0.0
    for i, order in enumerate(reversed(pipeline_orders)):
        weight = pipeline_weight ** i
        weighted_sum += order * weight
        weight_sum += weight

    if weight_sum > 0 and weighted_sum > 0:
        avg_pipeline_demand = weighted_sum / weight_sum
    else:
        avg_pipeline_demand = 100.0  # default estimate

    # Dynamic target with demand buffer
    dynamic_target = base_stock + safety_stock + (demand_buffer - 1.0) * avg_pipeline_demand

    # Calculate order with smoothing
    raw_order = dynamic_target - inventory_position
    order_amount = max(0, smoothing_factor * raw_order)

    # Apply order limits
    order_amount = max(min_order, min(max_order, order_amount))

    # Round to nearest integer
    return order_amount
