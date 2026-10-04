# policy_hash: 78c96a601be73fd54806ad6e1339840d77fc31670a264a8f9f1d807c89f003a7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1324.06
# best_prompt_performance: 1324.06
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_004647.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 510.0  # OPT_PARAM: {"initial": 510.0, "min": 450, "max": 600, "type": "float"}
    safety_stock = 45.0  # OPT_PARAM: {"initial": 45.0, "min": 30, "max": 70, "type": "float"}
    demand_forecast = 95.01244611736772  # OPT_PARAM: {"initial": 95.01244611736772, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.15, "type": "float"}

    # Calculate inventory position (standard definition)
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple order-up-to level
    order_up_to = base_stock + safety_stock

    # Calculate order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Smooth ordering
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = max(0, int(smoothed_order + 0.5))

    return order_amount
