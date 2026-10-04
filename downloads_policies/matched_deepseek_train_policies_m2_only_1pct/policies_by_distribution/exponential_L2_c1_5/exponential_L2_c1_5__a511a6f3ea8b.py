# policy_hash: a511a6f3ea8b43310f476dc9e07e3a5acab98f0c428d4c53bf1296af5919a11f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 34
# source_prompt_files: 2
# best_target_performance: 10223.65
# best_prompt_performance: 10223.65
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_073131.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 396.21005958397575  # OPT_PARAM: {"initial": 396.21005958397575, "min": 200, "max": 600, "type": "float"}
    safety_multiplier = 2.8  # OPT_PARAM: {"initial": 2.8, "min": 1.0, "max": 5.0, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    min_order_threshold = 15.953972010976061  # OPT_PARAM: {"initial": 15.953972010976061, "min": 5, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand variability from recent pipeline orders
    if len(pipeline_orders) >= 2:
        # Use last 3 orders if available, otherwise use all
        recent_orders = pipeline_orders[:min(3, len(pipeline_orders))]
        if len(recent_orders) > 1:
            mean_order = sum(recent_orders) / len(recent_orders)
            variance = sum((x - mean_order) ** 2 for x in recent_orders) / len(recent_orders)
            std_dev = variance ** 0.5
        else:
            std_dev = 0
    else:
        std_dev = 0

    # Calculate safety stock based on variability
    safety_stock = safety_multiplier * std_dev

    # Target inventory position
    target_position = base_stock + safety_stock

    # Calculate required order
    gap = target_position - inventory_position

    # Apply adjustment factor and ensure non-negative
    if gap > min_order_threshold:
        order_amount = max(0, gap * adjustment_factor)
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
