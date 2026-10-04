# policy_hash: 95c38752ae132369bc6d432d007ddc66196830ccc7c51cccd3e313732dcf68d4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 703.92
# best_prompt_performance: 703.92
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_225316.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 303.5290646616314  # OPT_PARAM: {"initial": 303.5290646616314, "min": 280, "max": 340, "type": "float"}
    safety_stock = 45.0  # OPT_PARAM: {"initial": 45.0, "min": 30, "max": 55, "type": "float"}
    demand_forecast = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.15, "type": "float"}
    lead_time_factor = 1.35  # OPT_PARAM: {"initial": 1.35, "min": 1.1, "max": 1.6, "type": "float"}
    threshold_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.6, "max": 0.9, "type": "float"}
    pipeline_weight = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.7, "max": 1.0, "type": "float"}
    min_order = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 5.0, "max": 20.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight ** i for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Adjust safety stock based on lead time
    adjusted_safety = safety_stock * lead_time_factor

    # Calculate order-up-to level
    order_up_to = max(base_stock, demand_forecast + adjusted_safety)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply threshold-based smoothing with minimum order constraint
    if raw_order > demand_forecast * threshold_factor:
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = raw_order

    # Ensure minimum order size
    final_order = max(smoothed_order, min_order)

    # Round to nearest integer
    order_amount = int(round(final_order))

    return order_amount
