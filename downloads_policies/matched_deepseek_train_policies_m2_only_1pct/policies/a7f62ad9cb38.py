# policy_hash: a7f62ad9cb3888aa1f6fc80f7fc0af8f076ffdd13d3c95008249a180f5eb8125
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 1253.98
# best_prompt_performance: 1253.62
# best_rel_error_pct: 0.028709
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_231752.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 259.34161037810634  # OPT_PARAM: {"initial": 259.34161037810634, "min": 200, "max": 350, "type": "float"}
    safety_stock = 25.678923477446833  # OPT_PARAM: {"initial": 25.678923477446833, "min": 20, "max": 80, "type": "float"}
    smoothing_factor = 0.3908627756391493  # OPT_PARAM: {"initial": 0.3908627756391493, "min": 0.3, "max": 0.9, "type": "float"}
    lead_time = 2  # OPT_PARAM: {"initial": 2, "min": 1, "max": 3, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time (using historical average)
    avg_demand = 84.54313878195747  # OPT_PARAM: {"initial": 84.54313878195747, "min": 80, "max": 120, "type": "float"}
    expected_lead_time_demand = lead_time * avg_demand

    # Dynamic target based on pipeline and expected demand
    target_position = base_stock + safety_stock + expected_lead_time_demand

    # Calculate raw order needed
    raw_order = target_position - inventory_position

    # Apply smoothing only for positive orders
    if raw_order > 0:
        smoothed_order = smoothing_factor * raw_order
    else:
        smoothed_order = raw_order

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
