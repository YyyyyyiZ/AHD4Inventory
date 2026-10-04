# policy_hash: c10a0a095e3b5d67846f77e8dcb2896579fd86592104c60c97ca65337244b632
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 11289.72
# best_prompt_performance: 11289.72
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_010402.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 343.969122248319  # OPT_PARAM: {"initial": 343.969122248319, "min": 300, "max": 700, "type": "float"}
    safety_stock = 45.57805230568093  # OPT_PARAM: {"initial": 45.57805230568093, "min": 30, "max": 200, "type": "float"}
    demand_forecast_factor = 0.44542958319525283  # OPT_PARAM: {"initial": 0.44542958319525283, "min": 0.1, "max": 1.5, "type": "float"}
    smoothing_factor = 0.07155963692386928  # OPT_PARAM: {"initial": 0.07155963692386928, "min": 0.05, "max": 0.5, "type": "float"}
    lead_time_factor = 1.0899642853012863  # OPT_PARAM: {"initial": 1.0899642853012863, "min": 0.5, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast using average of recent pipeline orders
    if pipeline_orders:
        # Use only recent orders for forecast (last 2 periods)
        recent_orders = pipeline_orders[-2:] if len(pipeline_orders) >= 2 else pipeline_orders
        avg_recent_demand = sum(recent_orders) / len(recent_orders)
    else:
        avg_recent_demand = 0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand * lead_time_factor

    # Add safety stock
    order_up_to = adjusted_base_stock + safety_stock

    # Calculate raw order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    if pipeline_orders:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
    else:
        smoothed_order = raw_order

    # Reasonable order limit based on forecast
    max_order_limit = 600.0  # OPT_PARAM: {"initial": 600.0, "min": 300, "max": 1000, "type": "float"}
    smoothed_order = min(smoothed_order, max_order_limit)

    # Ensure minimum order quantity for efficiency
    min_order_quantity = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 50, "type": "float"}
    if smoothed_order > 0 and smoothed_order < min_order_quantity:
        smoothed_order = min_order_quantity

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
