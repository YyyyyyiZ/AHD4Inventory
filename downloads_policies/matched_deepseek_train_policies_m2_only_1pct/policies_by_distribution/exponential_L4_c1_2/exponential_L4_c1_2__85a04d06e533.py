# policy_hash: 85a04d06e5339e93f352e1226e9b1cf702f0ee92f9b17693cdcd4d73ec73c4d1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 36
# source_prompt_files: 1
# best_target_performance: 6184.04
# best_prompt_performance: 6184.04
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_234758.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 272.5286178920232  # OPT_PARAM: {"initial": 272.5286178920232, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 34.80830782840767  # OPT_PARAM: {"initial": 34.80830782840767, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.9172910024208962  # OPT_PARAM: {"initial": 0.9172910024208962, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    if len(pipeline_orders) >= 2:
        recent_arrivals = pipeline_orders[:2]  # Oldest orders (recently arrived/arriving)
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = base_stock / 4  # Fallback

    # Adjust base stock based on demand trend
    adjusted_base_stock = base_stock + demand_forecast_factor * (avg_recent_demand - base_stock/4)

    # Add safety stock
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * last_order
        order_amount = max(0, smoothed_order)

    # Round to nearest integer (as order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
