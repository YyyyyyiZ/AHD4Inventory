# policy_hash: 0cd2598d87dd3225649d2c7acd4390c0f7c5421971ff5ac981e38819194ecf52
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1213.25
# best_prompt_performance: 1213.43
# best_rel_error_pct: 0.014836
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_095431.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 480.0  # OPT_PARAM: {"initial": 480.0, "min": 400, "max": 480, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 0.95, "type": "float"}
    smoothing_factor = 0.30000000000000004  # OPT_PARAM: {"initial": 0.30000000000000004, "min": 0.1, "max": 0.4, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 5, "type": "int"}
    safety_stock = 35.0  # OPT_PARAM: {"initial": 35.0, "min": 15, "max": 35, "type": "float"}
    demand_anticipation = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.2, "max": 0.4, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock with safety stock
    adjusted_base = base_stock + safety_stock

    # Simple base stock policy
    raw_order = adjusted_base - inventory_position
    order_amount = max(min_order, raw_order)

    # Apply smoothing to reduce volatility
    if order_amount > 0:
        smoothed_order = smoothing_factor * order_amount
        order_amount = max(min_order, smoothed_order)

    return order_amount
