# policy_hash: 93c854c639858dba88b9971db272eeae1d358c26854e8bbc86354a0254b5da4a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 3878.69
# best_prompt_performance: 3877.62
# best_rel_error_pct: 0.027587
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_005804.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 320.0  # OPT_PARAM: {"initial": 320.0, "min": 250, "max": 400, "type": "float"}
    demand_forecast = 80.1  # OPT_PARAM: {"initial": 80.1, "min": 80, "max": 130, "type": "float"}
    pipeline_coverage_factor = 1.1857587575428385  # OPT_PARAM: {"initial": 1.1857587575428385, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    safety_stock_factor = 1.0040689264164835  # OPT_PARAM: {"initial": 1.0040689264164835, "min": 1.0, "max": 3.0, "type": "float"}
    demand_variability_factor = 0.10406892641648345  # OPT_PARAM: {"initial": 0.10406892641648345, "min": 0.1, "max": 0.8, "type": "float"}
    immediate_buffer = 0.006103389624497702  # OPT_PARAM: {"initial": 0.006103389624497702, "min": 0.0, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    expected_demand_during_lead_time = demand_forecast * lead_time

    # Calculate safety stock with variability adjustment
    safety_stock = safety_stock_factor * demand_forecast * (1 + demand_variability_factor)

    # Calculate target inventory position
    target_inventory_position = base_stock + safety_stock

    # Adjust for pipeline coverage
    if expected_demand_during_lead_time > 0:
        pipeline_coverage = sum(pipeline_orders) / expected_demand_during_lead_time
        adjustment = pipeline_coverage_factor * min(1.0, pipeline_coverage)
        adjusted_target = target_inventory_position * (1 - adjustment)
    else:
        adjusted_target = target_inventory_position

    # Calculate base order
    base_order = max(0, adjusted_target - inventory_position)

    # Smooth with demand forecast
    order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_forecast

    # Add immediate buffer
    order_amount += immediate_buffer * demand_forecast

    # Ensure non-negative and integer
    order_amount = max(0, int(round(order_amount)))

    return order_amount
