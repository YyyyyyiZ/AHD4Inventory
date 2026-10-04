# policy_hash: ca5797efce647778c9c453f5a4835b45235faa44846a2f608c4f5b37cc64a52c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 3751.07
# best_prompt_performance: 3751.07
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_081424.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 723.873515168965  # OPT_PARAM: {"initial": 723.873515168965, "min": 400, "max": 900, "type": "float"}
    safety_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 3.0, "type": "float"}
    demand_forecast_window = 10  # OPT_PARAM: {"initial": 10, "min": 5, "max": 20, "type": "int"}
    smoothing_factor = 0.12698148392179567  # OPT_PARAM: {"initial": 0.12698148392179567, "min": 0.1, "max": 0.8, "type": "float"}
    lead_time = 6
    min_order_threshold = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 50, "type": "float"}

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
        safety_stock = safety_factor * (demand_variance ** 0.5) * (lead_time ** 0.5)
    else:
        safety_stock = safety_factor * avg_recent_demand * 0.5 * (lead_time ** 0.5)

    # Target inventory position = lead time demand + safety stock
    target_inventory = avg_recent_demand * lead_time + safety_stock

    # Clamp target to reasonable range relative to base stock
    target_inventory = max(base_stock * 0.8, min(base_stock * 1.2, target_inventory))

    # Calculate desired order
    desired_order = max(0, target_inventory - inventory_position)

    # Smooth ordering with recent demand pattern
    order_amount = smoothing_factor * desired_order + (1 - smoothing_factor) * avg_recent_demand

    # Apply minimum order threshold to reduce small orders
    if order_amount < min_order_threshold:
        order_amount = 0

    # Round to nearest integer
    return order_amount
