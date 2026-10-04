# policy_hash: 1411281525b457c3891f5d37578845b9b110e4e69c06e62739a249ee4bd2512a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 10401.67
# best_prompt_performance: 10394.9
# best_rel_error_pct: 0.065086
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_072425.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 325.77748388794294  # OPT_PARAM: {"initial": 325.77748388794294, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.851041483143625  # OPT_PARAM: {"initial": 50.851041483143625, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.7122485075211505  # OPT_PARAM: {"initial": 0.7122485075211505, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    # Use average of recent pipeline arrivals as demand proxy
    if len(pipeline_orders) >= 2:
        recent_arrivals = pipeline_orders[:2]  # Last two arrivals
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = base_stock / 6  # Fallback estimate

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock * demand_forecast_factor + safety_stock

    # Calculate order amount with smoothing
    target_order = max(0, adjusted_base_stock - inventory_position)

    # Smooth ordering to avoid extreme fluctuations
    smoothing_factor = 0.48921406829254793  # OPT_PARAM: {"initial": 0.48921406829254793, "min": 0.1, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * target_order + (1 - smoothing_factor) * last_order
    else:
        smoothed_order = target_order

    # Round to nearest integer (orders must be integers)
    order_amount = int(round(smoothed_order))

    # Ensure order doesn't exceed reasonable bounds
    max_order = 1000  # OPT_PARAM: {"initial": 1000, "min": 100, "max": 2000, "type": "int"}
    order_amount = min(order_amount, max_order)

    return order_amount
