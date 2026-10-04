# policy_hash: 486f8bf0b077eb512073c01d91d1846dd1f2494e6950f0d88b7c752e3f93a0f6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 10167.81
# best_prompt_performance: 10167.8
# best_rel_error_pct: 0.000098
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_074445.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 399.81832355056713  # OPT_PARAM: {"initial": 399.81832355056713, "min": 300, "max": 550, "type": "float"}
    safety_multiplier = 3.2  # OPT_PARAM: {"initial": 3.2, "min": 2.0, "max": 4.5, "type": "float"}
    adjustment_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.9, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.4, "type": "float"}
    demand_estimate_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent pipeline orders (these reflect past orders based on demand)
    if len(pipeline_orders) >= 2:
        # Use last 2 periods of pipeline orders as demand proxy
        recent_orders = pipeline_orders[:2]
        mean_order = sum(recent_orders) / len(recent_orders)
        variance = sum((x - mean_order) ** 2 for x in recent_orders) / len(recent_orders)
        std_dev = variance ** 0.5 if variance > 0 else 0
        demand_estimate = mean_order * demand_estimate_weight
    else:
        std_dev = 0
        demand_estimate = 0

    # Calculate safety stock
    safety_stock = safety_multiplier * std_dev

    # Adjust base stock based on pipeline status
    pipeline_total = sum(pipeline_orders)
    pipeline_ratio = pipeline_total / (base_stock * len(pipeline_orders)) if len(pipeline_orders) > 0 else 1.0
    adjusted_base = base_stock * (1.0 - pipeline_weight * (pipeline_ratio - 1.0))

    # Incorporate demand estimate into target
    target_position = max(adjusted_base, demand_estimate) + safety_stock

    # Calculate order amount
    gap = target_position - inventory_position
    if gap > 0:
        # Apply adjustment factor for smoother ordering
        order_amount = max(0, gap * adjustment_factor)
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
