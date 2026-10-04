# policy_hash: 3fe6ed09eabe45d10f462b8d0d74c327fe61a7e836c7b8392ccdd1872a50c919
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 6
# source_prompt_files: 2
# best_target_performance: 6908.33
# best_prompt_performance: 6908.02
# best_rel_error_pct: 0.004487
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_040517.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 278.91955744309854  # OPT_PARAM: {"initial": 278.91955744309854, "min": 250, "max": 350, "type": "float"}
    safety_stock = 21.191252363070813  # OPT_PARAM: {"initial": 21.191252363070813, "min": 0, "max": 50, "type": "float"}
    pipeline_factor = 0.25  # OPT_PARAM: {"initial": 0.25, "min": 0.05, "max": 0.25, "type": "float"}
    demand_forecast_factor = 0.63172197729229  # OPT_PARAM: {"initial": 0.63172197729229, "min": 0.5, "max": 1.2, "type": "float"}
    adjustment_smoothing = 0.19626307528681888  # OPT_PARAM: {"initial": 0.19626307528681888, "min": 0.1, "max": 0.5, "type": "float"}
    recent_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.3, "max": 0.8, "type": "float"}
    mid_weight = 0.29155611120381386  # OPT_PARAM: {"initial": 0.29155611120381386, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Improved demand forecast using weighted average of pipeline orders
    # Simpler weighting scheme focused on recent orders
    if pipeline_orders:
        if len(pipeline_orders) >= 2:
            weights = [recent_weight, mid_weight] + [0.1] * max(0, len(pipeline_orders) - 2)
            weights = weights[:len(pipeline_orders)]
            # Normalize weights
            weight_sum = sum(weights)
            if weight_sum > 0:
                weights = [w/weight_sum for w in weights]
        else:
            weights = [1.0]

        weighted_sum = sum(w * p for w, p in zip(weights, pipeline_orders))
        forecast_demand = weighted_sum * demand_forecast_factor
    else:
        forecast_demand = 0

    # Adjust base stock based on pipeline variability with smoothing
    if pipeline_orders and len(pipeline_orders) > 1:
        pipeline_avg = sum(pipeline_orders) / len(pipeline_orders)
        if pipeline_avg > 0:
            # Simpler variability measure
            pipeline_variability = max(pipeline_orders) / pipeline_avg - 1
            adjustment = 1 + min(pipeline_variability * pipeline_factor, 0.3)
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
