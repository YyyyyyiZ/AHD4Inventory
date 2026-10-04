# policy_hash: c4e365f3787b386b6fe361ad610561b2c04277e866d61d49e0da66d7d63b8718
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 6903.32
# best_prompt_performance: 6898.94
# best_rel_error_pct: 0.063448
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_041850.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 272.03329278382654  # OPT_PARAM: {"initial": 272.03329278382654, "min": 240, "max": 290, "type": "float"}
    safety_stock = 19.83817332687855  # OPT_PARAM: {"initial": 19.83817332687855, "min": 5, "max": 30, "type": "float"}
    pipeline_factor = 0.21527558258914184  # OPT_PARAM: {"initial": 0.21527558258914184, "min": 0.1, "max": 0.25, "type": "float"}
    demand_forecast_factor = 0.737073024889436  # OPT_PARAM: {"initial": 0.737073024889436, "min": 0.6, "max": 0.9, "type": "float"}
    adjustment_smoothing = 0.30039368941299655  # OPT_PARAM: {"initial": 0.30039368941299655, "min": 0.15, "max": 0.35, "type": "float"}
    recent_weight = 0.6956274709877369  # OPT_PARAM: {"initial": 0.6956274709877369, "min": 0.5, "max": 0.8, "type": "float"}
    mid_weight = 0.3003936894134624  # OPT_PARAM: {"initial": 0.3003936894134624, "min": 0.15, "max": 0.35, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Improved demand forecast using weighted average of pipeline orders
    if pipeline_orders:
        if len(pipeline_orders) >= 2:
            weights = [recent_weight, mid_weight] + [0.1] * max(0, len(pipeline_orders) - 2)
            weights = weights[:len(pipeline_orders)]
            weight_sum = sum(weights)
            if weight_sum > 0:
                weights = [w/weight_sum for w in weights]
        else:
            weights = [1.0]

        weighted_sum = sum(w * p for w, p in zip(weights, pipeline_orders))
        forecast_demand = weighted_sum * demand_forecast_factor
    else:
        forecast_demand = 0

    # Adjust base stock based on pipeline variability
    if pipeline_orders and len(pipeline_orders) > 1:
        pipeline_avg = sum(pipeline_orders) / len(pipeline_orders)
        if pipeline_avg > 0:
            pipeline_variability = max(pipeline_orders) / pipeline_avg - 1
            adjustment = 1 + min(pipeline_variability * pipeline_factor, 0.25)
            adjusted_base = base_stock * (adjustment_smoothing * adjustment + (1 - adjustment_smoothing))
        else:
            adjusted_base = base_stock
    else:
        adjusted_base = base_stock

    # Target inventory with forecast and safety stock
    target_inventory = adjusted_base + safety_stock + forecast_demand

    # Calculate order amount with integer rounding
    order_amount = max(0, round(target_inventory - inventory_position))

    return order_amount
