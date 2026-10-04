# policy_hash: 695110b323025d664ca6600caf3f0539474297a07e586aa839503a60968e556f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 697.99
# best_prompt_performance: 697.99
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_023330.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 321.6984448442618  # OPT_PARAM: {"initial": 321.6984448442618, "min": 200, "max": 400, "type": "float"}
    safety_stock = 55.502796783276644  # OPT_PARAM: {"initial": 55.502796783276644, "min": 0, "max": 100, "type": "float"}
    demand_forecast = 90.54138809801465  # OPT_PARAM: {"initial": 90.54138809801465, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.7808371491549061  # OPT_PARAM: {"initial": 0.7808371491549061, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected pipeline coverage
    expected_pipeline_coverage = sum(pipeline_orders) / max(1, len(pipeline_orders))

    # Adjust base stock based on pipeline status
    pipeline_adjustment = pipeline_weight * expected_pipeline_coverage

    # Calculate order-up-to level
    order_up_to = base_stock + safety_stock - pipeline_adjustment

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid extreme orders
    smoothing_factor = 0.9562762152467327  # OPT_PARAM: {"initial": 0.9562762152467327, "min": 0.5, "max": 1.0, "type": "float"}
    max_order_multiplier = 1.0645604480668145  # OPT_PARAM: {"initial": 1.0645604480668145, "min": 1.0, "max": 2.0, "type": "float"}

    max_reasonable_order = max_order_multiplier * demand_forecast
    if order_amount > max_reasonable_order:
        order_amount = smoothing_factor * max_reasonable_order + (1 - smoothing_factor) * order_amount

    return order_amount
