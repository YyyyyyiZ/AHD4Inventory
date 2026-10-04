# policy_hash: 6b027ed02d5c052c9c1b68e9ee44d948a5d722f501ce3f2a2b93803304c5c19f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 701.45
# best_prompt_performance: 701.32
# best_rel_error_pct: 0.018533
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260129_204655.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 314.4482125588757  # OPT_PARAM: {"initial": 314.4482125588757, "min": 200, "max": 350, "type": "float"}
    safety_stock = 35.0  # OPT_PARAM: {"initial": 35.0, "min": 15, "max": 70, "type": "float"}
    demand_buffer = 7.898009887187015  # OPT_PARAM: {"initial": 7.898009887187015, "min": 5, "max": 40, "type": "float"}
    smoothing_min = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 30, "type": "float"}
    smoothing_max = 97.26076499237469  # OPT_PARAM: {"initial": 97.26076499237469, "min": 80, "max": 200, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Dynamic adjustment based on pipeline status
    if pipeline_orders[0] > 0:  # Arrival happening this period
        # Reduce base stock when arrival occurs to avoid overstocking
        adjusted_base = base_stock - demand_buffer
    else:
        # Increase base stock when no arrival to maintain safety
        adjusted_base = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, adjusted_base - inventory_position)

    # Apply smoothing with refined bounds
    if order_amount > 0:
        order_amount = max(smoothing_min, min(order_amount, smoothing_max))

    return order_amount
