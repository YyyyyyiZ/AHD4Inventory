# policy_hash: 9a5cfbb4cc228bf2900caf93a78d69d06b9648f703bbf940bf5ba7df4e9c841b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 19
# source_prompt_files: 1
# best_target_performance: 6118.94
# best_prompt_performance: 6118.94
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_041932.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 267.9333385613566  # OPT_PARAM: {"initial": 267.9333385613566, "min": 150, "max": 400, "type": "float"}
    demand_window = 10  # OPT_PARAM: {"initial": 10, "min": 4, "max": 15, "type": "int"}
    safety_factor = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.5, "max": 3.5, "type": "float"}
    smoothing_factor = 0.15  # OPT_PARAM: {"initial": 0.15, "min": 0.15, "max": 0.8, "type": "float"}
    pipeline_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.3, "max": 0.9, "type": "float"}
    forecast_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 1.0, "type": "float"}
    min_order = 5  # OPT_PARAM: {"initial": 5, "min": 0, "max": 30, "type": "int"}
    lost_sales_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}
    holding_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use pipeline arrivals as demand proxy (historical orders reflect past demand)
    if len(pipeline_orders) >= demand_window:
        recent_arrivals = pipeline_orders[:demand_window]
    else:
        recent_arrivals = pipeline_orders if pipeline_orders else [0]

    # Calculate demand forecast using exponential smoothing
    if recent_arrivals:
        forecast = recent_arrivals[0]
        for arrival in recent_arrivals[1:]:
            forecast = forecast_weight * arrival + (1 - forecast_weight) * forecast
    else:
        forecast = base_stock * 0.2

    # Calculate safety stock based on demand variability
    if len(recent_arrivals) >= 3:
        avg_demand = sum(recent_arrivals) / len(recent_arrivals)
        demand_variance = sum((r - avg_demand) ** 2 for r in recent_arrivals) / len(recent_arrivals)
        safety_stock = safety_factor * (demand_variance ** 0.5)
    else:
        safety_stock = safety_factor * forecast * 0.3

    # Adjust base stock with cost-ratio awareness
    # Higher lost-sales cost (p=2) vs holding cost (h=1) suggests we should carry more inventory
    cost_adjusted_base = base_stock * (1 + lost_sales_weight * (2/3) - holding_weight * (1/3))

    # Final adjusted base stock
    adjusted_base_stock = cost_adjusted_base + safety_stock + forecast * 0.5

    # Consider pipeline content in target calculation
    pipeline_content = sum(pipeline_orders)
    pipeline_adjustment = pipeline_weight * pipeline_content

    # Calculate target inventory position
    target_inventory_position = adjusted_base_stock - pipeline_adjustment

    # Calculate order needed
    order_needed = target_inventory_position - inventory_position

    # Apply smoothing
    smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * forecast

    # Ensure minimum order quantity and non-negative
    order_amount = int(round(max(min_order, smoothed_order)))

    return order_amount
