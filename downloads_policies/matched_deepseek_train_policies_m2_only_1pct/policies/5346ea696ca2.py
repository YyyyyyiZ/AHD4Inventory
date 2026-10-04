# policy_hash: 5346ea696ca2d8ef57fc5dd6c64f56e0e771266487de912ca73d3ec12aa5de32
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 46
# source_prompt_files: 1
# best_target_performance: 3753.58
# best_prompt_performance: 3753.58
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_080940.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 822.7494618294016  # OPT_PARAM: {"initial": 822.7494618294016, "min": 400, "max": 900, "type": "float"}
    safety_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 3.0, "type": "float"}
    demand_forecast_window = 15  # OPT_PARAM: {"initial": 15, "min": 5, "max": 20, "type": "int"}
    smoothing_factor = 0.12566807208647782  # OPT_PARAM: {"initial": 0.12566807208647782, "min": 0.1, "max": 0.8, "type": "float"}
    lead_time = 6

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use recent pipeline arrivals as proxy for demand
    recent_orders = pipeline_orders[-min(demand_forecast_window, len(pipeline_orders)):]
    if recent_orders:
        avg_recent_demand = sum(recent_orders) / len(recent_orders)
    else:
        avg_recent_demand = base_stock / lead_time

    # Calculate safety stock based on demand variability
    if len(recent_orders) > 1:
        demand_variance = sum((x - avg_recent_demand) ** 2 for x in recent_orders) / len(recent_orders)
        safety_stock = safety_factor * (demand_variance ** 0.5)
    else:
        safety_stock = safety_factor * avg_recent_demand * 0.5

    # Target inventory position = lead time demand + safety stock
    target_inventory = avg_recent_demand * lead_time + safety_stock

    # Clamp target to reasonable range relative to base stock
    target_inventory = max(base_stock * 0.7, min(base_stock * 1.3, target_inventory))

    # Calculate desired order
    desired_order = max(0, target_inventory - inventory_position)

    # Smooth ordering with recent demand pattern
    order_amount = smoothing_factor * desired_order + (1 - smoothing_factor) * avg_recent_demand

    # Round to nearest integer
    return order_amount
