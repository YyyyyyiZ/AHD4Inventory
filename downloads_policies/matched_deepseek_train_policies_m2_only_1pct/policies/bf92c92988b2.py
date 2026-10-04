# policy_hash: bf92c92988b2bd60566d157f1f126ae87ea3b2e71e75bc4f136f29720cbfa4a6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 10163.5
# best_prompt_performance: 10163.65
# best_rel_error_pct: 0.001476
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_073656.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 369.00747657081143  # OPT_PARAM: {"initial": 369.00747657081143, "min": 200, "max": 600, "type": "float"}
    safety_multiplier = 2.8  # OPT_PARAM: {"initial": 2.8, "min": 1.0, "max": 5.0, "type": "float"}
    adjustment_factor = 0.4342793578031296  # OPT_PARAM: {"initial": 0.4342793578031296, "min": 0.3, "max": 1.0, "type": "float"}
    pipeline_weight = 0.13185947144577798  # OPT_PARAM: {"initial": 0.13185947144577798, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand variability from recent pipeline orders
    if len(pipeline_orders) >= 2:
        # Use recent orders (last 3 or all available)
        recent_orders = pipeline_orders[:min(3, len(pipeline_orders))]
        if len(recent_orders) > 1:
            mean_order = sum(recent_orders) / len(recent_orders)
            variance = sum((x - mean_order) ** 2 for x in recent_orders) / len(recent_orders)
            std_dev = variance ** 0.5
        else:
            std_dev = 0
    else:
        std_dev = 0

    # Calculate safety stock
    safety_stock = safety_multiplier * std_dev

    # Adjust base stock based on pipeline status
    # If pipeline is low, be more aggressive; if high, be conservative
    pipeline_ratio = sum(pipeline_orders) / (base_stock * len(pipeline_orders)) if len(pipeline_orders) > 0 else 1.0
    adjusted_base = base_stock * (1.0 - pipeline_weight * (pipeline_ratio - 1.0))

    # Target inventory position
    target_position = adjusted_base + safety_stock

    # Calculate order amount
    gap = target_position - inventory_position
    if gap > 0:
        # Apply adjustment factor for smoother ordering
        order_amount = max(0, gap * adjustment_factor)
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
