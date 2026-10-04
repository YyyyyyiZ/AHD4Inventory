# policy_hash: 352ee3465c7c892ae0a08e76db23f98a86e9485d1b5120318601badef11eceaa
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 18
# source_prompt_files: 1
# best_target_performance: 6115.2
# best_prompt_performance: 6115.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_042327.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 273.96681539584023  # OPT_PARAM: {"initial": 273.96681539584023, "min": 200, "max": 350, "type": "float"}
    demand_window = 8  # OPT_PARAM: {"initial": 8, "min": 5, "max": 12, "type": "int"}
    safety_factor = 1.901730787672193  # OPT_PARAM: {"initial": 1.901730787672193, "min": 1.8, "max": 3.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.4, "type": "float"}
    pipeline_weight = 0.7331597112897849  # OPT_PARAM: {"initial": 0.7331597112897849, "min": 0.4, "max": 0.8, "type": "float"}
    forecast_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}
    min_order = 10  # OPT_PARAM: {"initial": 10, "min": 0, "max": 20, "type": "int"}
    lost_sales_weight = 0.7199703169685627  # OPT_PARAM: {"initial": 0.7199703169685627, "min": 0.6, "max": 1.2, "type": "float"}
    holding_weight = 0.15293131680149186  # OPT_PARAM: {"initial": 0.15293131680149186, "min": 0.05, "max": 0.25, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use pipeline arrivals as demand proxy
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
        forecast = base_stock * 0.15

    # Calculate safety stock based on demand variability
    if len(recent_arrivals) >= 4:
        avg_demand = sum(recent_arrivals) / len(recent_arrivals)
        demand_variance = sum((r - avg_demand) ** 2 for r in recent_arrivals) / len(recent_arrivals)
        safety_stock = safety_factor * (demand_variance ** 0.5)
    else:
        safety_stock = safety_factor * forecast * 0.25

    # Cost-adjusted base stock considering p=2, h=1
    cost_adjusted_base = base_stock * (1 + lost_sales_weight * (2/3) - holding_weight * (1/3))

    # Final adjusted base stock
    adjusted_base_stock = cost_adjusted_base + safety_stock + forecast * 0.4

    # Pipeline adjustment
    pipeline_content = sum(pipeline_orders)
    pipeline_adjustment = pipeline_weight * pipeline_content

    # Target inventory position
    target_inventory_position = adjusted_base_stock - pipeline_adjustment

    # Order needed
    order_needed = target_inventory_position - inventory_position

    # Apply smoothing
    smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * forecast

    # Ensure minimum order and non-negative
    order_amount = int(round(max(min_order, smoothed_order)))

    return order_amount
