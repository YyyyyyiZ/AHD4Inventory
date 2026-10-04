# policy_hash: aaee6e50f1f717e9c37702a2805baf4dc50ab5a385350af5a910b8290a9a9bb9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 5936.56
# best_prompt_performance: 5936.56
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_104718.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 133.1788141520227  # OPT_PARAM: {"initial": 133.1788141520227, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 81.95342526849808  # OPT_PARAM: {"initial": 81.95342526849808, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    # (pipeline_orders[0] arrived today, pipeline_orders[1] arrives tomorrow)
    if len(pipeline_orders) >= 2:
        recent_arrivals = pipeline_orders[0] + pipeline_orders[1]
        forecast_adjustment = demand_forecast_factor * recent_arrivals / 2
    else:
        forecast_adjustment = 0

    # Adjust base stock level based on forecast
    adjusted_base_stock = base_stock + forecast_adjustment

    # Calculate order amount with safety stock consideration
    target_inventory = adjusted_base_stock + safety_stock
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.179941553614392  # OPT_PARAM: {"initial": 0.179941553614392, "min": 0.1, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * last_order

    # Round to nearest integer (orders must be integer quantities)
    order_amount = int(round(order_amount))

    return order_amount
