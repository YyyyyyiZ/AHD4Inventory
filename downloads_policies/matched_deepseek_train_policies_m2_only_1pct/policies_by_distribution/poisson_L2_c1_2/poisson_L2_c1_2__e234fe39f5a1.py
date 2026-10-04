# policy_hash: e234fe39f5a1d6d75b3f915bf55de00e098d1db182a54b7e001b3632a0659189
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 825.87
# best_prompt_performance: 825.87
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_023734.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 319.78711564514333  # OPT_PARAM: {"initial": 319.78711564514333, "min": 250, "max": 320, "type": "float"}
    safety_stock = 56.71765778109232  # OPT_PARAM: {"initial": 56.71765778109232, "min": 20, "max": 60, "type": "float"}
    demand_forecast = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.0, "type": "float"}

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
    smoothing_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.7, "max": 0.9, "type": "float"}
    max_order_multiplier = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 1.1, "max": 1.5, "type": "float"}

    max_reasonable_order = max_order_multiplier * demand_forecast
    if order_amount > max_reasonable_order:
        order_amount = smoothing_factor * max_reasonable_order + (1 - smoothing_factor) * order_amount

    return order_amount
