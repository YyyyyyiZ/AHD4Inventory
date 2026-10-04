# policy_hash: 008130c084592f7e256cde23d80269806f7111f5cad7e62035ce06a86f0a1189
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 30
# source_prompt_files: 1
# best_target_performance: 11079.08
# best_prompt_performance: 11078.68
# best_rel_error_pct: 0.003610
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_045339.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 435.677359030067  # OPT_PARAM: {"initial": 435.677359030067, "min": 300, "max": 700, "type": "float"}
    safety_stock = 105.67735903006289  # OPT_PARAM: {"initial": 105.67735903006289, "min": 50, "max": 250, "type": "float"}
    demand_forecast_factor = 0.7359577653041155  # OPT_PARAM: {"initial": 0.7359577653041155, "min": 0.5, "max": 1.5, "type": "float"}
    smoothing_factor = 0.24249235519602155  # OPT_PARAM: {"initial": 0.24249235519602155, "min": 0.1, "max": 0.8, "type": "float"}
    order_threshold = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 10, "max": 100, "type": "float"}
    lead_time_demand_factor = 2.150797791336335  # OPT_PARAM: {"initial": 2.150797791336335, "min": 1.5, "max": 4.0, "type": "float"}
    pipeline_weight = 0.7404716332186811  # OPT_PARAM: {"initial": 0.7404716332186811, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted average of recent pipeline orders
    if len(pipeline_orders) > 0:
        # Give more weight to recent orders
        weighted_sum = 0
        total_weight = 0
        for i, order in enumerate(pipeline_orders):
            weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
            weighted_sum += order * weight
            total_weight += weight

        if total_weight > 0:
            avg_pipeline = weighted_sum / total_weight
        else:
            avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)

        forecast_demand = avg_pipeline * demand_forecast_factor * lead_time_demand_factor
    else:
        forecast_demand = 0

    # Dynamic base stock adjustment
    adjusted_base_stock = base_stock + safety_stock + forecast_demand

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing only for larger orders
    if order_amount > order_threshold:
        order_amount = smoothing_factor * order_amount

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
