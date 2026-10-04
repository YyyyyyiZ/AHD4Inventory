# policy_hash: 81b041e29c515032e1d3f61533c3d43755592b3fc95a15aceb18e13d0109fc9a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1530.86
# best_prompt_performance: 1530.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_034934.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 281.5718225509528  # OPT_PARAM: {"initial": 281.5718225509528, "min": 200, "max": 400, "type": "float"}
    safety_stock = 16.57182255095317  # OPT_PARAM: {"initial": 16.57182255095317, "min": 0, "max": 50, "type": "float"}
    demand_forecast = 103.13798282506262  # OPT_PARAM: {"initial": 103.13798282506262, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.3782581304065133  # OPT_PARAM: {"initial": 0.3782581304065133, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_forecast * len(pipeline_orders)

    # Calculate target inventory position
    target_position = base_stock + safety_stock + expected_demand_during_leadtime

    # Smooth ordering to reduce volatility
    order_gap = target_position - inventory_position
    if order_gap > 0:
        order_amount = max(0, smoothing_factor * order_gap)
    else:
        order_amount = 0

    return order_amount
