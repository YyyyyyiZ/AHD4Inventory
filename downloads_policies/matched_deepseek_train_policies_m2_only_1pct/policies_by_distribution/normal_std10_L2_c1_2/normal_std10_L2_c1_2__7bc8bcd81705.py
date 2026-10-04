# policy_hash: 7bc8bcd81705fa85b6184c1c941d142743f0794508db8f480e3f95f44a465170
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 913.78
# best_prompt_performance: 913.78
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260129_204444.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 310.0  # OPT_PARAM: {"initial": 310.0, "min": 200, "max": 400, "type": "float"}
    safety_stock = 25.0  # OPT_PARAM: {"initial": 25.0, "min": 10, "max": 60, "type": "float"}
    demand_buffer = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 40, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline status
    if pipeline_orders[0] > 0:  # Arrival happening this period
        adjusted_base = base_stock - demand_buffer
    else:
        adjusted_base = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, adjusted_base - inventory_position)

    # Apply smoothing to avoid extreme order sizes
    if order_amount > 0:
        order_amount = max(10, min(order_amount, 150))  # OPT_PARAM: {"initial": 150, "min": 100, "max": 250, "type": "float"}

    return order_amount
