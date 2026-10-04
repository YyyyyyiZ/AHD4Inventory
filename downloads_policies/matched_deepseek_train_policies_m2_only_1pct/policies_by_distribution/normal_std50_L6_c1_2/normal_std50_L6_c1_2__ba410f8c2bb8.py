# policy_hash: ba410f8c2bb84313c459eaf7a6c287c253478828eb8ae1f840dca29eee00cab4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 3725.05
# best_prompt_performance: 3725.05
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_085027.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 727.7269748071311  # OPT_PARAM: {"initial": 727.7269748071311, "min": 600, "max": 900, "type": "float"}
    safety_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 2.5, "type": "float"}
    demand_forecast_window = 12  # OPT_PARAM: {"initial": 12, "min": 8, "max": 20, "type": "int"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    lead_time = 6
    min_order_threshold = 5.0  # OPT_PARAM: {"initial": 5.0, "min": 0, "max": 20, "type": "float"}
    demand_floor = 40.05530342258354  # OPT_PARAM: {"initial": 40.05530342258354, "min": 30, "max": 80, "type": "float"}
    max_order_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.0, "type": "float"}

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

    # Keep target within reasonable bounds relative to base stock
    target_inventory = max(base_stock * 0.8, min(base_stock * max_order_multiplier, target_inventory))

    # Calculate desired order
    desired_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce volatility
    order_amount = smoothing_factor * desired_order + (1 - smoothing_factor) * avg_recent_demand

    # Apply minimum order threshold
    if order_amount < min_order_threshold:
        order_amount = 0

    # Round to nearest integer
    return order_amount
