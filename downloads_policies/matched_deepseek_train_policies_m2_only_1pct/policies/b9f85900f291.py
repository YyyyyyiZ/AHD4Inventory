# policy_hash: b9f85900f291a8ab4fe606389df9a1639735c0bdb5d8deaf0d26f805b51e0b30
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 18
# source_prompt_files: 1
# best_target_performance: 6109.96
# best_prompt_performance: 6110.04
# best_rel_error_pct: 0.001309
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_042115.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 326.58293005602394  # OPT_PARAM: {"initial": 326.58293005602394, "min": 200, "max": 400, "type": "float"}
    demand_window = 10  # OPT_PARAM: {"initial": 10, "min": 5, "max": 15, "type": "int"}
    safety_factor = 2.931535563354846  # OPT_PARAM: {"initial": 2.931535563354846, "min": 1.5, "max": 3.0, "type": "float"}
    smoothing_factor = 0.12418068398458333  # OPT_PARAM: {"initial": 0.12418068398458333, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}
    forecast_weight = 0.3289221342158773  # OPT_PARAM: {"initial": 0.3289221342158773, "min": 0.3, "max": 0.9, "type": "float"}
    min_order = 5  # OPT_PARAM: {"initial": 5, "min": 0, "max": 20, "type": "int"}
    max_order = 500  # OPT_PARAM: {"initial": 500, "min": 300, "max": 800, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use pipeline arrivals as demand proxy (most recent arrivals)
    if len(pipeline_orders) >= demand_window:
        recent_arrivals = pipeline_orders[:demand_window]
    else:
        recent_arrivals = pipeline_orders if pipeline_orders else [0]

    # Calculate demand forecast using weighted moving average
    if recent_arrivals:
        # Weighted moving average with exponential decay
        weights = [forecast_weight ** i for i in range(len(recent_arrivals))]
        weights = [w / sum(weights) for w in weights]
        forecast = sum(r * w for r, w in zip(recent_arrivals, weights))
    else:
        forecast = base_stock * 0.2

    # Calculate safety stock based on demand variability
    if len(recent_arrivals) >= 3:
        avg_demand = sum(recent_arrivals) / len(recent_arrivals)
        demand_variance = sum((r - avg_demand) ** 2 for r in recent_arrivals) / len(recent_arrivals)
        safety_stock = safety_factor * (demand_variance ** 0.5)
    else:
        safety_stock = safety_factor * forecast * 0.4

    # Adjust base stock with safety stock and forecast
    adjusted_base_stock = base_stock + safety_stock + forecast * 0.3

    # Consider pipeline content in target calculation
    pipeline_content = sum(pipeline_orders)
    pipeline_adjustment = pipeline_weight * pipeline_content

    # Calculate target inventory position
    target_inventory_position = adjusted_base_stock - pipeline_adjustment

    # Calculate order needed
    order_needed = target_inventory_position - inventory_position

    # Apply smoothing with stronger emphasis on current gap
    smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * forecast

    # Apply bounds and ensure non-negative
    order_amount = int(round(max(min_order, min(max_order, smoothed_order))))

    return order_amount
