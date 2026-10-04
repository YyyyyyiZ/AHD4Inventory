# policy_hash: bd197c5e0053a7cef33849b86a3c40761c9d2050e3ff82d1ddb944d9010842f7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 926.56
# best_prompt_performance: 926.54
# best_rel_error_pct: 0.002159
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223903.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 293.85430088270357  # OPT_PARAM: {"initial": 293.85430088270357, "min": 250, "max": 320, "type": "float"}
    safety_stock = 28.0  # OPT_PARAM: {"initial": 28.0, "min": 15, "max": 45, "type": "float"}
    demand_forecast = 101.87532924227047  # OPT_PARAM: {"initial": 101.87532924227047, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.0, "max": 0.2, "type": "float"}
    smoothing_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simpler pipeline adjustment using only the next arrival
    if len(pipeline_orders) >= 1:
        next_arrival = pipeline_orders[0]
        # Reduce base stock adjustment when next arrival is high
        if next_arrival > demand_forecast:
            adjusted_base = base_stock - pipeline_weight * (next_arrival - demand_forecast)
        else:
            adjusted_base = base_stock
    else:
        adjusted_base = base_stock

    # Calculate order-up-to level
    order_up_to = max(adjusted_base, demand_forecast + safety_stock)

    # Calculate order amount with stronger smoothing
    raw_order = max(0, order_up_to - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure order amount is integer
    order_amount = int(round(smoothed_order))

    return order_amount
