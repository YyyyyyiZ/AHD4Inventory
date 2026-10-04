# policy_hash: baff75ecf8d1a041e8352c31666a194a553c6452a51d21092239e7d46adb7cfd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 716.38
# best_prompt_performance: 716.38
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_225728.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 279.9433043394498  # OPT_PARAM: {"initial": 279.9433043394498, "min": 200, "max": 350, "type": "float"}
    safety_stock = 35.0  # OPT_PARAM: {"initial": 35.0, "min": 20, "max": 60, "type": "float"}
    demand_forecast = 96.02140668415551  # OPT_PARAM: {"initial": 96.02140668415551, "min": 90, "max": 110, "type": "float"}
    lead_time_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.8, "max": 1.5, "type": "float"}
    smoothing_factor = 0.04218231697694244  # OPT_PARAM: {"initial": 0.04218231697694244, "min": 0.0, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate order-up-to level with lead-time adjusted safety stock
    order_up_to = demand_forecast + safety_stock * lead_time_factor

    # Use the maximum of base_stock and calculated order-up-to
    target_level = max(base_stock, order_up_to)

    # Calculate raw order amount
    raw_order = max(0, target_level - inventory_position)

    # Apply smoothing to reduce order volatility
    if raw_order > 0:
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
