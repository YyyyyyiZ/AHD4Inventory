# policy_hash: 2d501b11c9c0cfce088fc50c4e1da571a9d6fb38157652a46754f27c89db70de
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 24
# source_prompt_files: 1
# best_target_performance: 3941.41
# best_prompt_performance: 3941.08
# best_rel_error_pct: 0.008373
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_004615.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 550.0  # OPT_PARAM: {"initial": 550.0, "min": 400, "max": 700, "type": "float"}
    demand_forecast = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 130, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    safety_stock_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.5, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety stock
    lead_time = len(pipeline_orders)
    expected_demand_during_lead_time = demand_forecast * lead_time
    safety_stock = safety_stock_factor * demand_forecast

    # Calculate target inventory position
    target_inventory_position = expected_demand_during_lead_time + safety_stock

    # Adjust target based on pipeline coverage
    pipeline_coverage = sum(pipeline_orders) / max(1, expected_demand_during_lead_time)
    adjusted_target = target_inventory_position * (1 - pipeline_weight * min(1, pipeline_coverage))

    # Calculate base order
    base_order = max(0, adjusted_target - inventory_position)

    # Smooth with demand forecast
    order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_forecast

    # Ensure non-negative and integer
    order_amount = max(0, int(round(order_amount)))

    return order_amount
