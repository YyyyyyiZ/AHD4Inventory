# policy_hash: 36af3396625009f18a43c38b201189578d743720e86f9c56c50032bfcb4c0e38
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 11196.99
# best_prompt_performance: 11207.08
# best_rel_error_pct: 0.090114
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_084334.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 431.6232646235009  # OPT_PARAM: {"initial": 431.6232646235009, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 32.623330843723416  # OPT_PARAM: {"initial": 32.623330843723416, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline orders (as a proxy for recent demand)
    # Use average of recent pipeline arrivals as demand estimate
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[:min(3, len(pipeline_orders))]
        avg_recent_demand = sum(recent_orders) / len(recent_orders)
    else:
        avg_recent_demand = 0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand

    # Calculate order amount with safety stock adjustment
    order_amount = max(0, adjusted_base_stock + safety_stock - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.1520838154061262  # OPT_PARAM: {"initial": 0.1520838154061262, "min": 0.1, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_pipeline
        order_amount = max(0, smoothed_order)

    # Round to nearest integer (as order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
