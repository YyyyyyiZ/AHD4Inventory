# policy_hash: 4f4fe391db7505584088ecadeeca3e8e4799ae028f381f8f2a843bcb9765d9d5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 716.44
# best_prompt_performance: 716.44
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_224022.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 291.36184868053147  # OPT_PARAM: {"initial": 291.36184868053147, "min": 250, "max": 400, "type": "float"}
    safety_stock = 25.0  # OPT_PARAM: {"initial": 25.0, "min": 10, "max": 60, "type": "float"}
    demand_forecast = 95.60295999670043  # OPT_PARAM: {"initial": 95.60295999670043, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    lead_time_factor = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 0.8, "max": 1.5, "type": "float"}
    lost_sales_weight = 1.8  # OPT_PARAM: {"initial": 1.8, "min": 1.2, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust safety stock based on lead time and lost sales weight
    adjusted_safety = safety_stock * lead_time_factor * lost_sales_weight

    # Calculate order-up-to level with safety adjustment
    order_up_to = max(base_stock, demand_forecast + adjusted_safety)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing to reduce order volatility
    if raw_order > 0:
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
