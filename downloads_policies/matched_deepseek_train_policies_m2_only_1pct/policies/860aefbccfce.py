# policy_hash: 860aefbccfce796b505565ca19392867372b323ba29f031f404fb071a9334b0d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1246.39
# best_prompt_performance: 1246.39
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_012407.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 825.4741176299136  # OPT_PARAM: {"initial": 825.4741176299136, "min": 700, "max": 1000, "type": "float"}
    safety_stock = 73.86795442617088  # OPT_PARAM: {"initial": 73.86795442617088, "min": 50, "max": 120, "type": "float"}
    demand_forecast = 90.5593354525226  # OPT_PARAM: {"initial": 90.5593354525226, "min": 90, "max": 110, "type": "float"}
    adjustment_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.3, "type": "float"}
    reorder_point = 550.0970389102198  # OPT_PARAM: {"initial": 550.0970389102198, "min": 400, "max": 700, "type": "float"}
    max_order = 100.73224839147727  # OPT_PARAM: {"initial": 100.73224839147727, "min": 100, "max": 200, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = expected_lead_time_demand + safety_stock

    # Blend base_stock and target_inventory based on pipeline status
    effective_base = (pipeline_weight * base_stock +
                     (1 - pipeline_weight) * target_inventory)

    # Calculate raw order amount
    raw_order = max(0, effective_base - inventory_position)

    # Apply reorder point logic: only order if inventory position is below threshold
    if inventory_position > reorder_point:
        raw_order = max(0, raw_order * 0.5)

    # Apply smoothing
    smoothed_order = (smoothing_factor * raw_order +
                     (1 - smoothing_factor) * demand_forecast)

    # Apply adjustment factor and cap maximum order
    order_amount = max(0, min(adjustment_factor * smoothed_order, max_order))

    # Round to nearest integer
    return order_amount
