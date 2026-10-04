# policy_hash: c9b38c4848d3aeac88481c90aa23cbbf509e9d6634450b0dfeecd14a3983872e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 10161.49
# best_prompt_performance: 10161.49
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_074746.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 422.7232449562226  # OPT_PARAM: {"initial": 422.7232449562226, "min": 350, "max": 600, "type": "float"}
    safety_multiplier = 2.8  # OPT_PARAM: {"initial": 2.8, "min": 1.5, "max": 4.0, "type": "float"}
    adjustment_factor = 0.34303962200739235  # OPT_PARAM: {"initial": 0.34303962200739235, "min": 0.3, "max": 0.9, "type": "float"}
    pipeline_weight = 0.11422374225800037  # OPT_PARAM: {"initial": 0.11422374225800037, "min": 0.1, "max": 0.5, "type": "float"}
    demand_estimate_weight = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.5, "max": 1.2, "type": "float"}
    min_order_threshold = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 5.0, "max": 50.0, "type": "float"}
    max_order_multiplier = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.0, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent pipeline orders
    if len(pipeline_orders) >= 2:
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
    if gap > min_order_threshold:
        # Apply adjustment factor with upper bound
        raw_order = gap * adjustment_factor
        max_order = base_stock * max_order_multiplier
        order_amount = min(max(0, raw_order), max_order)
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
