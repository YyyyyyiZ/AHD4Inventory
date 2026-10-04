# policy_hash: 5768e12b2955d439cf9b873460cc96142692f7a08db3d062aa7cadb62eb0a223
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 2
# best_target_performance: 4650.61
# best_prompt_performance: 4652.26
# best_rel_error_pct: 0.035479
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_225541.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 534.2731889632475  # OPT_PARAM: {"initial": 534.2731889632475, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.32133416307758  # OPT_PARAM: {"initial": 50.32133416307758, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.3401781844240327  # OPT_PARAM: {"initial": 0.3401781844240327, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected shortfall with smoothing
    expected_shortfall = max(0, base_stock - inventory_position)

    # Add safety stock adjustment
    adjusted_shortfall = expected_shortfall + safety_stock

    # Apply smoothing to avoid large order swings
    order_amount = max(0, smoothing_factor * adjusted_shortfall)

    return order_amount
