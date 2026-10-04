# policy_hash: bd457b9ca7c4876acd32aa9fd350a41f8a3e29a51dd74c5b519a45065530b7eb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 866.55
# best_prompt_performance: 866.55
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_023659.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 217.86238754368617  # OPT_PARAM: {"initial": 217.86238754368617, "min": 180, "max": 280, "type": "float"}
    safety_stock = 82.86238754368459  # OPT_PARAM: {"initial": 82.86238754368459, "min": 40, "max": 120, "type": "float"}
    demand_forecast = 98.5  # OPT_PARAM: {"initial": 98.5, "min": 85, "max": 115, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate order-up-to level with dynamic adjustment
    # Reduce base stock when pipeline has significant inventory
    pipeline_total = sum(pipeline_orders)
    pipeline_adjustment = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    adjusted_base = base_stock - pipeline_adjustment * pipeline_total

    # Dynamic safety stock based on pipeline variability
    if len(pipeline_orders) >= 2:
        pipeline_range = max(pipeline_orders) - min(pipeline_orders)
        variability_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.8, "type": "float"}
        dynamic_safety = safety_stock + variability_factor * pipeline_range
    else:
        dynamic_safety = safety_stock

    order_up_to = max(demand_forecast, adjusted_base + dynamic_safety)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Progressive smoothing based on order size
    smoothing_threshold = 119.93022865262526  # OPT_PARAM: {"initial": 119.93022865262526, "min": 80, "max": 200, "type": "float"}
    max_smoothing = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.3, "max": 0.9, "type": "float"}

    if order_amount > smoothing_threshold:
        # More aggressive smoothing for larger orders
        excess_ratio = min(1.0, (order_amount - smoothing_threshold) / 100.0)
        smoothing_factor = max_smoothing * excess_ratio
        order_amount = smoothing_factor * smoothing_threshold + (1 - smoothing_factor) * order_amount

    # Round to nearest integer
    return order_amount
