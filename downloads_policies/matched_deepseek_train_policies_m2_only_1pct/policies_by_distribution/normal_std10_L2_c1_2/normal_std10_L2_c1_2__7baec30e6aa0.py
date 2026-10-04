# policy_hash: 7baec30e6aa03f8897bf68bd26aad985e0f7116c54a2fcd0cb920dab7e9d48e5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 66
# source_prompt_files: 1
# best_target_performance: 695.62
# best_prompt_performance: 695.62
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260129_204935.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 308.88233561483213  # OPT_PARAM: {"initial": 308.88233561483213, "min": 280, "max": 330, "type": "float"}
    safety_stock = 45.0  # OPT_PARAM: {"initial": 45.0, "min": 30, "max": 60, "type": "float"}
    demand_buffer = 11.807766262785693  # OPT_PARAM: {"initial": 11.807766262785693, "min": 10, "max": 25, "type": "float"}
    smoothing_min = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 5, "max": 20, "type": "float"}
    smoothing_max = 98.38909022000023  # OPT_PARAM: {"initial": 98.38909022000023, "min": 90, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Dynamic adjustment based on pipeline status
    if pipeline_orders[0] > 0:  # Arrival happening this period
        # More conservative reduction to prevent stockouts
        adjusted_base = base_stock - (demand_buffer * 0.7)
    else:
        # More aggressive safety stock when no arrival
        adjusted_base = base_stock + (safety_stock * 1.2)

    # Calculate order amount
    order_amount = max(0, adjusted_base - inventory_position)

    # Apply smoothing with refined bounds
    if order_amount > 0:
        order_amount = max(smoothing_min, min(order_amount, smoothing_max))

    return order_amount
