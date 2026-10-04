# policy_hash: ea4e59a4fe583bcf279df92039f5140bbc7488f8a87f37d03cd0fee7a751849a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 31
# source_prompt_files: 2
# best_target_performance: 6187.0
# best_prompt_performance: 6187.0
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_035005.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 277.77126188020657  # OPT_PARAM: {"initial": 277.77126188020657, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 44.907806796598734  # OPT_PARAM: {"initial": 44.907806796598734, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    if len(pipeline_orders) > 0:
        recent_arrivals = pipeline_orders[:min(3, len(pipeline_orders))]
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = 0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand

    # Calculate target inventory position
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme orders
    smoothing_factor = 0.27572852566233885  # OPT_PARAM: {"initial": 0.27572852566233885, "min": 0.1, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount

    # Round to nearest integer (since order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
