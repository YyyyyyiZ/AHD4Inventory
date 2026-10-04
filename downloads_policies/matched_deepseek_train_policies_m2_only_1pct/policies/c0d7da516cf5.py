# policy_hash: c0d7da516cf51fac975bef13896dd0508d808279ab188cc83d13b7196ae2d690
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 4909.76
# best_prompt_performance: 4928.64
# best_rel_error_pct: 0.384540
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_003924.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 424.66137911768396  # OPT_PARAM: {"initial": 424.66137911768396, "min": 350, "max": 500, "type": "float"}
    safety_stock = 24.42602787907168  # OPT_PARAM: {"initial": 24.42602787907168, "min": 10, "max": 60, "type": "float"}
    demand_forecast_factor = 0.6561876780994822  # OPT_PARAM: {"initial": 0.6561876780994822, "min": 0.6, "max": 1.2, "type": "float"}
    pipeline_weight = 0.5503080587725051  # OPT_PARAM: {"initial": 0.5503080587725051, "min": 0.3, "max": 0.9, "type": "float"}
    recent_window = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 6, "type": "int"}
    adjustment_factor = 0.6089732703907191  # OPT_PARAM: {"initial": 0.6089732703907191, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use weighted average of recent pipeline orders as demand forecast
    if len(pipeline_orders) > 0:
        recent_arrivals = pipeline_orders[:recent_window]
        weights = [pipeline_weight ** i for i in range(len(recent_arrivals))]
        weighted_sum = sum(w * d for w, d in zip(weights, recent_arrivals))
        weight_sum = sum(weights)
        avg_recent_demand = weighted_sum / weight_sum if weight_sum > 0 else 0
    else:
        avg_recent_demand = 0

    # Adjust base stock based on demand forecast with smoother adjustment
    adjusted_base = base_stock + demand_forecast_factor * avg_recent_demand

    # Additional adjustment based on current pipeline status
    pipeline_total = sum(pipeline_orders)
    if pipeline_total > 0:
        pipeline_ratio = pipeline_total / (base_stock + 1)
        pipeline_adjustment = adjustment_factor * (1.0 - pipeline_ratio)
        adjusted_base += pipeline_adjustment * base_stock

    # Calculate target inventory position
    target_position = adjusted_base + safety_stock

    # Calculate order amount with smoother adjustment
    order_amount = max(0, target_position - inventory_position)

    # Apply conservative rounding (floor to avoid over-ordering)
    return order_amount
