# policy_hash: f65011fa5e0216325acc63362b80b1aa974c8bae2c34fbfda120c329410cd084
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 10184.67
# best_prompt_performance: 10184.53
# best_rel_error_pct: 0.001375
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_074652.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 413.09378396589005  # OPT_PARAM: {"initial": 413.09378396589005, "min": 300, "max": 550, "type": "float"}
    safety_multiplier = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 0.5, "max": 3.0, "type": "float"}
    adjustment_factor = 0.4245891511271474  # OPT_PARAM: {"initial": 0.4245891511271474, "min": 0.3, "max": 1.0, "type": "float"}
    min_order_threshold = 5.777686025356803  # OPT_PARAM: {"initial": 5.777686025356803, "min": 0, "max": 30, "type": "float"}
    demand_estimate_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent pipeline orders (these reflect past decisions)
    if len(pipeline_orders) >= 2:
        # Use last 2 orders as demand proxy
        recent_orders = pipeline_orders[:2]
        mean_order = sum(recent_orders) / len(recent_orders)
        # Simple variability estimate
        variability = max(recent_orders) - min(recent_orders) if len(recent_orders) > 1 else 0
    else:
        mean_order = 0
        variability = 0

    # Dynamic base stock adjustment based on demand estimate
    adjusted_base = base_stock * (1 + demand_estimate_weight * (mean_order / (base_stock + 1)))

    # Safety stock based on variability
    safety_stock = safety_multiplier * variability

    # Target inventory position
    target_position = adjusted_base + safety_stock

    # Calculate required order
    gap = target_position - inventory_position

    # Apply adjustment factor with threshold
    if gap > min_order_threshold:
        order_amount = max(0, gap * adjustment_factor)
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
