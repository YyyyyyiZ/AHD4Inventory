# policy_hash: 1e5610d4a3e356c0ae022201bf9c857ee53d459d1070e01d010aaa152f9522b0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 28
# source_prompt_files: 1
# best_target_performance: 11083.96
# best_prompt_performance: 11084.58
# best_rel_error_pct: 0.005594
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_085639.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 484.73594950943743  # OPT_PARAM: {"initial": 484.73594950943743, "min": 350, "max": 600, "type": "float"}
    pipeline_weight = 0.8225852768914821  # OPT_PARAM: {"initial": 0.8225852768914821, "min": 0.8, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.7, "type": "float"}
    safety_stock = 38.56160882026427  # OPT_PARAM: {"initial": 38.56160882026427, "min": 20, "max": 80, "type": "float"}
    demand_buffer = 1.169995057047517  # OPT_PARAM: {"initial": 1.169995057047517, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate base order amount with demand buffer
    order_amount = max(0, base_stock * demand_buffer - inventory_position)

    # Add safety stock adjustment based on pipeline variability
    if len(pipeline_orders) >= 2:
        recent_avg = sum(pipeline_orders[-2:]) / 2
        if recent_avg > 100:  # Moderate threshold for safety stock addition
            order_amount += safety_stock

    # Apply smoothing
    order_amount = smoothing_factor * order_amount

    # Ensure minimum order when inventory is very low
    if inventory_position < base_stock * 0.3:
        order_amount = max(order_amount, safety_stock * 0.5)

    # Round to nearest integer (orders should be discrete units)
    order_amount = int(round(order_amount))

    return order_amount
