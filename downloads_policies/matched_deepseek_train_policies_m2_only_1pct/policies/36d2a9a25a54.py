# policy_hash: 36d2a9a25a54b000dea8f52af044fe3de33c487d315f31c31ffafa0d6aedd347
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 3725.38
# best_prompt_performance: 3725.35
# best_rel_error_pct: 0.000805
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_083252.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 683.2314192272416  # OPT_PARAM: {"initial": 683.2314192272416, "min": 400, "max": 900, "type": "float"}
    safety_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 3.0, "type": "float"}
    demand_forecast_window = 15  # OPT_PARAM: {"initial": 15, "min": 5, "max": 20, "type": "int"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    lead_time = 6
    min_order_threshold = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 50, "type": "float"}
    demand_floor = 38.60070186444859  # OPT_PARAM: {"initial": 38.60070186444859, "min": 20, "max": 100, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use recent pipeline arrivals as proxy for demand
    recent_orders = pipeline_orders[-min(demand_forecast_window, len(pipeline_orders)):]
    if recent_orders:
        avg_recent_demand = sum(recent_orders) / len(recent_orders)
        # Apply floor to prevent underestimation
        avg_recent_demand = max(avg_recent_demand, demand_floor)
    else:
        avg_recent_demand = base_stock / lead_time

    # Calculate safety stock with more conservative approach
    if len(recent_orders) > 1:
        demand_variance = sum((x - avg_recent_demand) ** 2 for x in recent_orders) / len(recent_orders)
        safety_stock = safety_factor * (demand_variance ** 0.5) * (lead_time ** 0.5)
    else:
        safety_stock = safety_factor * avg_recent_demand * 0.7 * (lead_time ** 0.5)

    # Target inventory position = lead time demand + safety stock
    target_inventory = avg_recent_demand * lead_time + safety_stock

    # Keep target within tighter bounds relative to base stock
    target_inventory = max(base_stock * 0.85, min(base_stock * 1.15, target_inventory))

    # Calculate desired order
    desired_order = max(0, target_inventory - inventory_position)

    # More aggressive smoothing to reduce volatility
    order_amount = smoothing_factor * desired_order + (1 - smoothing_factor) * avg_recent_demand

    # Apply minimum order threshold (lowered to reduce lost sales)
    if order_amount < min_order_threshold:
        order_amount = 0

    # Round to nearest integer
    return order_amount
