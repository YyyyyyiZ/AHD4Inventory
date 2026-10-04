# policy_hash: faa9f7a1d499f05641214ac4f4d4a3124b009ecef03371546ef749a62f5fe851
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 3883.31
# best_prompt_performance: 3883.66
# best_rel_error_pct: 0.009013
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_000356.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 418.11784498730157  # OPT_PARAM: {"initial": 418.11784498730157, "min": 300, "max": 550, "type": "float"}
    safety_stock = 58.1178449873011  # OPT_PARAM: {"initial": 58.1178449873011, "min": 20, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    demand_forecast_factor = 1.06297167183988  # OPT_PARAM: {"initial": 1.06297167183988, "min": 0.8, "max": 1.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast: average of last 3 pipeline arrivals (recent demand proxy)
    recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
    expected_demand = sum(recent_orders) / len(recent_orders) if recent_orders else 0

    # Adjust base stock with forecast
    adjusted_base_stock = base_stock + safety_stock + (expected_demand * demand_forecast_factor)

    # Calculate raw order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply simple exponential smoothing
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * expected_demand

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
