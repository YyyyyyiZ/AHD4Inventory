# policy_hash: 11a2f187f2d9be2f9340f631ee7a9f39974d809853b650033add01553ee1ab7e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 914.74
# best_prompt_performance: 914.74
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223231.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 295.79999999999785  # OPT_PARAM: {"initial": 295.79999999999785, "min": 100, "max": 400, "type": "float"}
    safety_stock = 35.0  # OPT_PARAM: {"initial": 35.0, "min": 0, "max": 100, "type": "float"}
    demand_forecast = 98.5  # OPT_PARAM: {"initial": 98.5, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate order-up-to level
    order_up_to = max(base_stock, demand_forecast + safety_stock)

    # Calculate order amount with smoothing
    raw_order = max(0, order_up_to - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
