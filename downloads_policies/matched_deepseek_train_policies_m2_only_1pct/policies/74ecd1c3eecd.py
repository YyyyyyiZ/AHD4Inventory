# policy_hash: 74ecd1c3eecd67db53569a058d490a1be87c534ce05dc252f735af7e8afdd40b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 3210.98
# best_prompt_performance: 3216.96
# best_rel_error_pct: 0.186236
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r9/prompt_for_code/m2_20260129_215128.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 692.9989373965938  # OPT_PARAM: {"initial": 692.9989373965938, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 49.999147368215766  # OPT_PARAM: {"initial": 49.999147368215766, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 100.00282493290453  # OPT_PARAM: {"initial": 100.00282493290453, "min": 50, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline coverage
    pipeline_coverage = sum(pipeline_orders[:3])  # Look at next 3 arrivals
    adjustment_factor = 0.9499886540463228  # OPT_PARAM: {"initial": 0.9499886540463228, "min": 0.5, "max": 1.5, "type": "float"}

    if pipeline_coverage < demand_forecast * 2:
        adjusted_base = base_stock * adjustment_factor
    else:
        adjusted_base = base_stock

    # Add safety stock buffer
    target_inventory = adjusted_base + safety_stock

    # Calculate order amount with smoothing
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme order sizes
    smoothing_factor = 0.5863214938911114  # OPT_PARAM: {"initial": 0.5863214938911114, "min": 0.1, "max": 1.0, "type": "float"}
    smoothed_order = smoothing_factor * raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
