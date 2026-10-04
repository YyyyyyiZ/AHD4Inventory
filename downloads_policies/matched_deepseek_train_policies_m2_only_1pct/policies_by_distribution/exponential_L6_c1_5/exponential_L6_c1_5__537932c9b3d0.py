# policy_hash: 537932c9b3d0a6d7ee65fba708f9d7723a2c4cb3e2ab32173f041bf6c5fcd4f8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 11900.07
# best_prompt_performance: 11900.07
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_060801.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 559.3985561298624  # OPT_PARAM: {"initial": 559.3985561298624, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 168.492885570987  # OPT_PARAM: {"initial": 168.492885570987, "min": 0, "max": 500, "type": "float"}
    pipeline_weight = 0.23661044748334545  # OPT_PARAM: {"initial": 0.23661044748334545, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on pipeline composition
    oldest_order_ratio = pipeline_orders[0] / (sum(pipeline_orders) + 1e-6) if sum(pipeline_orders) > 0 else 0
    pipeline_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0, "max": 0.5, "type": "float"}

    adjusted_base_stock = base_stock * pipeline_adjustment

    # Calculate order amount with safety stock buffer
    target_inventory = adjusted_base_stock + safety_stock
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme order sizes
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = order_amount * smoothing_factor

    # Round to integer (as required by output specification)
    return order_amount
