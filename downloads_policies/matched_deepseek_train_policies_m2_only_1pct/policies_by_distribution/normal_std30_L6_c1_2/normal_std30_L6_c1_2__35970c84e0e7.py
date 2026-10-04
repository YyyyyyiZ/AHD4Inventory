# policy_hash: 35970c84e0e748fd14b78307a413c4151a2923a762acbe31120ab11796381751
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 3474.5
# best_prompt_performance: 3477.26
# best_rel_error_pct: 0.079436
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_023349.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 595.1452215814055  # OPT_PARAM: {"initial": 595.1452215814055, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.32626977464053  # OPT_PARAM: {"initial": 50.32626977464053, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.37406676323180316  # OPT_PARAM: {"initial": 0.37406676323180316, "min": 0.1, "max": 2.0, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock adjustment
    target_inventory = base_stock + safety_stock

    # Adjust target based on pipeline status (more pipeline = lower target)
    pipeline_adjustment = pipeline_weight * (sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0)
    adjusted_target = target_inventory - pipeline_adjustment

    # Calculate order amount with smoothing
    raw_order = max(0, adjusted_target - inventory_position)

    # Apply demand forecast factor for smoother ordering
    order_amount = int(round(raw_order * demand_forecast_factor))

    return order_amount
