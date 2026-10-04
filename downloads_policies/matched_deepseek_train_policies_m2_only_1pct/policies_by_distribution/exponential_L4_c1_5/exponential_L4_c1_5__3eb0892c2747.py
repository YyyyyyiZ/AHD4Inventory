# policy_hash: 3eb0892c2747b687b743f9b5ef85a74ec2e4d7147e0599bfae74780c38d6404d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 24
# source_prompt_files: 1
# best_target_performance: 11070.73
# best_prompt_performance: 11070.98
# best_rel_error_pct: 0.002258
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_044957.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 428.20839299890594  # OPT_PARAM: {"initial": 428.20839299890594, "min": 300, "max": 700, "type": "float"}
    safety_stock = 98.20839299889975  # OPT_PARAM: {"initial": 98.20839299889975, "min": 50, "max": 250, "type": "float"}
    demand_forecast_factor = 0.7406458671948769  # OPT_PARAM: {"initial": 0.7406458671948769, "min": 0.5, "max": 1.5, "type": "float"}
    smoothing_factor = 0.2526790603983622  # OPT_PARAM: {"initial": 0.2526790603983622, "min": 0.1, "max": 0.8, "type": "float"}
    lead_time_demand_factor = 2.1430413852276313  # OPT_PARAM: {"initial": 2.1430413852276313, "min": 1.5, "max": 4.0, "type": "float"}
    order_threshold = 30.0  # OPT_PARAM: {"initial": 30.0, "min": 10, "max": 100, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate lead time demand using pipeline orders as proxy
    if len(pipeline_orders) > 0:
        # Use simple average of pipeline orders for demand estimation
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        forecast_demand = avg_pipeline * demand_forecast_factor * lead_time_demand_factor
    else:
        forecast_demand = 0

    # Dynamic base stock adjustment
    adjusted_base_stock = base_stock + safety_stock + forecast_demand

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing with threshold
    if order_amount > order_threshold:
        order_amount = smoothing_factor * order_amount

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
