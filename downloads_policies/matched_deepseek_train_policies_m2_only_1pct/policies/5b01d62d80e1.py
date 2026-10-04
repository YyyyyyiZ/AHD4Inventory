# policy_hash: 5b01d62d80e16daae3fe88c399f9b54a37f37e63157786c4309da29ca0eec7bc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 897.68
# best_prompt_performance: 897.68
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_035334.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 459.9999999997431  # OPT_PARAM: {"initial": 459.9999999997431, "min": 350, "max": 500, "type": "float"}
    safety_stock = 119.9  # OPT_PARAM: {"initial": 119.9, "min": 40, "max": 120, "type": "float"}
    smoothing_factor = 0.5103934602285891  # OPT_PARAM: {"initial": 0.5103934602285891, "min": 0.5, "max": 1.0, "type": "float"}
    demand_forecast_window = 10  # OPT_PARAM: {"initial": 10, "min": 5, "max": 20, "type": "int"}
    forecast_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    min_order_threshold = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 5.0, "max": 50.0, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate demand forecast based on recent pipeline arrivals
    # Use pipeline arrivals as proxy for recent demand
    recent_arrivals = pipeline_orders[:min(demand_forecast_window, len(pipeline_orders))]
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on demand forecast
    adjusted_base = base_stock + forecast_weight * (avg_recent_demand - 100)

    # Calculate desired order-up-to level
    desired_level = adjusted_base + safety_stock

    # Calculate raw order amount
    raw_order = smoothing_factor * (desired_level - inventory_position)

    # Apply threshold: only order if significant gap exists
    if raw_order < min_order_threshold:
        order_amount = 0
    else:
        order_amount = max(0, raw_order)

    return order_amount
