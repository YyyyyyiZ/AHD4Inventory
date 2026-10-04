# policy_hash: 257e70955022234ed2bcccd717635aacdede0e7e20be6c3ef1a0e9bf0cded454
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 38
# source_prompt_files: 1
# best_target_performance: 2360.42
# best_prompt_performance: 2360.28
# best_rel_error_pct: 0.005931
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_010819.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 605.460464451238  # OPT_PARAM: {"initial": 605.460464451238, "min": 400, "max": 900, "type": "float"}
    safety_stock = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 10, "max": 80, "type": "float"}
    demand_forecast_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.5, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast using recent pipeline orders
    if len(pipeline_orders) > 0:
        # Use last 3 periods if available
        recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
        avg_recent = sum(recent_orders) / len(recent_orders)
        forecast_demand = avg_recent * demand_forecast_factor
    else:
        forecast_demand = 0

    # Target inventory level
    target_inventory = base_stock + safety_stock + forecast_demand

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with historical average order
    if len(pipeline_orders) > 0:
        avg_past_order = sum(pipeline_orders) / len(pipeline_orders)
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * avg_past_order
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
