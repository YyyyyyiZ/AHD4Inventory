# policy_hash: be758ac2f159724e1432330f6c422b077841cba41f4657f950e4a87ece2a19bf
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 5888.16
# best_prompt_performance: 5888.16
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_224750.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 150.27744466367582  # OPT_PARAM: {"initial": 150.27744466367582, "min": 50, "max": 300, "type": "float"}
    safety_factor = 3.2738007647504443  # OPT_PARAM: {"initial": 3.2738007647504443, "min": 1.0, "max": 4.0, "type": "float"}
    pipeline_weight = 0.9553552352423222  # OPT_PARAM: {"initial": 0.9553552352423222, "min": 0.3, "max": 1.0, "type": "float"}
    smoothing_factor = 0.36990983562133395  # OPT_PARAM: {"initial": 0.36990983562133395, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand variability estimate using pipeline orders
    if len(pipeline_orders) >= 2:
        pipeline_mean = sum(pipeline_orders) / len(pipeline_orders)
        variance = sum((p - pipeline_mean) ** 2 for p in pipeline_orders) / len(pipeline_orders)
        std_dev = variance ** 0.5
    else:
        std_dev = base_stock * 0.25

    # Safety stock based on demand variability
    safety_stock = safety_factor * std_dev

    # Adjust target based on pipeline status
    # More conservative when pipeline is full
    total_pipeline = sum(pipeline_orders)
    expected_pipeline = base_stock * len(pipeline_orders) * pipeline_weight
    pipeline_adjustment = max(0, expected_pipeline - total_pipeline) * 0.5

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock + pipeline_adjustment

    # Order needed to reach target
    order_needed = target_inventory - inventory_position

    # Smooth large orders to avoid overreaction
    if abs(order_needed) > base_stock * 0.4:
        smoothed_order = order_needed * smoothing_factor
    else:
        smoothed_order = order_needed

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
