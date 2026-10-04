# policy_hash: 05cb28c308a373bdc2f1ccc585409270dc5b853921a1e8be3dc0b244c0994885
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 1508.34
# best_prompt_performance: 1508.34
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_081715.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 479.1343511422185  # OPT_PARAM: {"initial": 479.1343511422185, "min": 300, "max": 600, "type": "float"}
    demand_forecast = 98.65969322085466  # OPT_PARAM: {"initial": 98.65969322085466, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected shortfall
    expected_shortfall = max(0, base_stock - inventory_position)

    # Smooth adjustment based on demand forecast
    smoothed_order = smoothing_factor * expected_shortfall + (1 - smoothing_factor) * demand_forecast

    # Ensure non-negative order
    order_amount = max(0, round(smoothed_order))

    return order_amount
