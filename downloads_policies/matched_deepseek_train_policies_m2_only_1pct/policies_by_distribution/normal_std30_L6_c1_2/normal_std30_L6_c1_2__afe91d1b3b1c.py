# policy_hash: afe91d1b3b1cd5902732960c6cb72dc1074f436bb1497bd7f18297d48e74eeee
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 34
# source_prompt_files: 1
# best_target_performance: 2379.48
# best_prompt_performance: 2379.32
# best_rel_error_pct: 0.006724
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_010031.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 565.6012388315868  # OPT_PARAM: {"initial": 565.6012388315868, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 20.682287024815  # OPT_PARAM: {"initial": 20.682287024815, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.35295004810933345  # OPT_PARAM: {"initial": 0.35295004810933345, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand based on pipeline orders (proxy for recent demand)
    # Use average of recent orders as demand forecast
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
        avg_recent_demand = sum(recent_orders) / len(recent_orders)
        forecast_demand = avg_recent_demand * demand_forecast_factor
    else:
        forecast_demand = 0

    # Adjust base stock level based on demand forecast
    adjusted_base_stock = base_stock + forecast_demand + safety_stock

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to avoid extreme order variations
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        avg_past_order = sum(pipeline_orders) / len(pipeline_orders)
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_past_order
        order_amount = max(0, smoothed_order)

    # Round to nearest integer (as required by problem statement)
    order_amount = int(round(order_amount))

    return order_amount
