# policy_hash: 0fb682cf6caad1ef6232d86f58b648ba865d482d939dee0cc609218d1cf8594a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 19
# source_prompt_files: 1
# best_target_performance: 10170.44
# best_prompt_performance: 10170.44
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_074345.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 434.06665885169787  # OPT_PARAM: {"initial": 434.06665885169787, "min": 300, "max": 700, "type": "float"}
    safety_multiplier = 3.2  # OPT_PARAM: {"initial": 3.2, "min": 2.0, "max": 5.0, "type": "float"}
    adjustment_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 1.0, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    demand_estimate_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent pipeline orders (these reflect past orders based on demand)
    if len(pipeline_orders) >= 2:
        recent_orders = pipeline_orders[:min(4, len(pipeline_orders))]
        mean_order = sum(recent_orders) / len(recent_orders)
        variance = sum((x - mean_order) ** 2 for x in recent_orders) / len(recent_orders)
        std_dev = variance ** 0.5 if variance > 0 else 0
    else:
        mean_order = 0
        std_dev = 0

    # Calculate safety stock
    safety_stock = safety_multiplier * std_dev

    # Adjust base stock based on pipeline status
    pipeline_total = sum(pipeline_orders)
    pipeline_ratio = pipeline_total / (base_stock * len(pipeline_orders)) if len(pipeline_orders) > 0 else 1.0
    adjusted_base = base_stock * (1.0 - pipeline_weight * (pipeline_ratio - 1.0))

    # Incorporate demand estimate into target
    demand_adjustment = demand_estimate_weight * mean_order
    target_position = max(adjusted_base, demand_adjustment) + safety_stock

    # Calculate order amount
    gap = target_position - inventory_position
    if gap > 0:
        # Apply adjustment factor
        order_amount = max(0, gap * adjustment_factor)
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
