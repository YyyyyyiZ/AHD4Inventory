# policy_hash: d696b943bcef963d647d436e8c043586848a86a4dd905e7fda18a2e23e55e62c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 6122.9
# best_prompt_performance: 6122.74
# best_rel_error_pct: 0.002613
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_042505.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 286.75658998312923  # OPT_PARAM: {"initial": 286.75658998312923, "min": 200, "max": 350, "type": "float"}
    demand_window = 8  # OPT_PARAM: {"initial": 8, "min": 5, "max": 12, "type": "int"}
    safety_factor = 1.3541297776269403  # OPT_PARAM: {"initial": 1.3541297776269403, "min": 1.2, "max": 2.5, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.6, "type": "float"}
    forecast_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.2, "max": 0.6, "type": "float"}
    min_order = 10  # OPT_PARAM: {"initial": 10, "min": 0, "max": 20, "type": "int"}
    cost_ratio_adjust = 1.1359220620634254  # OPT_PARAM: {"initial": 1.1359220620634254, "min": 1.0, "max": 1.3, "type": "float"}
    forecast_boost = 0.29826994625498715  # OPT_PARAM: {"initial": 0.29826994625498715, "min": 0.2, "max": 0.6, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use pipeline arrivals as demand proxy
    if len(pipeline_orders) >= demand_window:
        recent_arrivals = pipeline_orders[:demand_window]
    else:
        recent_arrivals = pipeline_orders if pipeline_orders else [0]

    # Simple moving average forecast (more stable than exponential smoothing)
    if recent_arrivals:
        forecast = sum(recent_arrivals) / len(recent_arrivals)
    else:
        forecast = base_stock * 0.25

    # Calculate safety stock based on demand variability
    if len(recent_arrivals) >= 3:
        avg_demand = forecast
        demand_variance = sum((r - avg_demand) ** 2 for r in recent_arrivals) / len(recent_arrivals)
        safety_stock = safety_factor * (demand_variance ** 0.5)
    else:
        safety_stock = safety_factor * forecast * 0.4

    # Adjust base stock considering cost ratio (p=2, h=1)
    # Higher lost-sales cost suggests carrying more inventory
    cost_adjusted_base = base_stock * cost_ratio_adjust

    # Final adjusted base stock with forecast boost
    adjusted_base_stock = cost_adjusted_base + safety_stock + forecast * forecast_boost

    # Consider pipeline content in target calculation
    pipeline_content = sum(pipeline_orders)
    pipeline_adjustment = pipeline_weight * pipeline_content

    # Calculate target inventory position
    target_inventory_position = adjusted_base_stock - pipeline_adjustment

    # Calculate order needed
    order_needed = target_inventory_position - inventory_position

    # Apply smoothing to reduce order volatility
    smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * forecast

    # Ensure minimum order quantity and non-negative
    order_amount = int(round(max(min_order, smoothed_order)))

    return order_amount
