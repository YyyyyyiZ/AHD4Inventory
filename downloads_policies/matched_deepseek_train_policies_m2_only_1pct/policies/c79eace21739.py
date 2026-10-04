# policy_hash: c79eace217391652f7d95e9dd683e232b9c800de5c910eee26c903a72ec7af95
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2508.45
# best_prompt_performance: 2510.4
# best_rel_error_pct: 0.077737
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_062704.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 661.0173964605418  # OPT_PARAM: {"initial": 661.0173964605418, "min": 550, "max": 750, "type": "float"}
    safety_stock = 37.52653533934503  # OPT_PARAM: {"initial": 37.52653533934503, "min": 10, "max": 40, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.85, "max": 1.0, "type": "float"}
    demand_buffer = 29.241465883553587  # OPT_PARAM: {"initial": 29.241465883553587, "min": 5, "max": 30, "type": "float"}
    order_smoothing = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic target level with safety stock and demand buffer
    target_level = base_stock + safety_stock + demand_buffer

    # Calculate raw order amount
    raw_order = max(0, target_level - inventory_position)

    # Apply smoothing to reduce order volatility
    order_amount = int(round(order_smoothing * raw_order))

    return order_amount
