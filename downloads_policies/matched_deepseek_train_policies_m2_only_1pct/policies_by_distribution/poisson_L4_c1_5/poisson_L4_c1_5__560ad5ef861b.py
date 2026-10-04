# policy_hash: 560ad5ef861b1a6e64d8ad1c01ade6f058f2a4b28b20ed8b55ca0a5457f9e522
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 1230.32
# best_prompt_performance: 1230.32
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_005849.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 433.37507226059614  # OPT_PARAM: {"initial": 433.37507226059614, "min": 400, "max": 550, "type": "float"}
    safety_stock = 13.337507226059612  # OPT_PARAM: {"initial": 13.337507226059612, "min": 10, "max": 50, "type": "float"}
    demand_forecast = 96.67501445211923  # OPT_PARAM: {"initial": 96.67501445211923, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.010000000000000002  # OPT_PARAM: {"initial": 0.010000000000000002, "min": 0.01, "max": 0.1, "type": "float"}
    pipeline_weight = 0.8664997109576156  # OPT_PARAM: {"initial": 0.8664997109576156, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate weighted pipeline inventory (recent orders weighted more)
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
        weighted_pipeline += order * weight

    # Calculate effective inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Dynamic order-up-to level based on pipeline composition
    order_up_to = base_stock + safety_stock

    # Order-up-to with adaptive smoothing
    gap = order_up_to - inventory_position
    raw_order = max(0, gap)

    # Adjust smoothing based on gap size (more aggressive for larger gaps)
    if gap > demand_forecast * 2:
        effective_smoothing = min(0.1, smoothing_factor * 2)
    else:
        effective_smoothing = smoothing_factor

    smoothed_order = effective_smoothing * raw_order + (1 - effective_smoothing) * demand_forecast

    # Round to nearest integer with minimum order threshold
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
