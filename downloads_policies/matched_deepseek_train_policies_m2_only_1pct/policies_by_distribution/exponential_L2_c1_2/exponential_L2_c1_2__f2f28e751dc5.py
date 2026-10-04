# policy_hash: f2f28e751dc565835cd47e1d1dbf50daa86c5fa130aaf319fff9f755c02f97de
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 33
# source_prompt_files: 2
# best_target_performance: 5936.48
# best_prompt_performance: 5936.48
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_104840.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 176.3535986053774  # OPT_PARAM: {"initial": 176.3535986053774, "min": 50, "max": 400, "type": "float"}
    safety_stock = 25.0  # OPT_PARAM: {"initial": 25.0, "min": 10, "max": 100, "type": "float"}
    demand_forecast_factor = 0.49996379201680013  # OPT_PARAM: {"initial": 0.49996379201680013, "min": 0.1, "max": 2.0, "type": "float"}
    smoothing_factor = 0.19577774530217365  # OPT_PARAM: {"initial": 0.19577774530217365, "min": 0.1, "max": 1.0, "type": "float"}
    pipeline_weight_recent = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast: weighted average of pipeline orders
    if len(pipeline_orders) > 0:
        if len(pipeline_orders) >= 2:
            weights = [1 - pipeline_weight_recent, pipeline_weight_recent]
            weighted_sum = sum(w * p for w, p in zip(weights, pipeline_orders[-2:]))
            forecast_demand = weighted_sum
        else:
            forecast_demand = pipeline_orders[-1]
    else:
        forecast_demand = 0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * forecast_demand

    # Order-up-to level with safety stock
    order_up_to = max(adjusted_base_stock, safety_stock)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing
    if len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_order
        order_amount = max(0, smoothed_order)

    return order_amount
