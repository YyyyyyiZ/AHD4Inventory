# policy_hash: 8d51357e8342cf1cd62c6c1f78f880660ae3f88a07ac6f96983792f38f9e22f1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 704.2
# best_prompt_performance: 704.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_224334.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 294.98144794900077  # OPT_PARAM: {"initial": 294.98144794900077, "min": 250, "max": 350, "type": "float"}
    safety_stock = 35.0  # OPT_PARAM: {"initial": 35.0, "min": 20, "max": 60, "type": "float"}
    demand_forecast = 95.30613224368848  # OPT_PARAM: {"initial": 95.30613224368848, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    lead_time_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.8, "max": 1.5, "type": "float"}
    threshold_factor = 0.8058894645365186  # OPT_PARAM: {"initial": 0.8058894645365186, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate adjusted safety stock
    adjusted_safety = safety_stock * lead_time_factor

    # Calculate order-up-to level with dynamic adjustment
    order_up_to = max(base_stock, demand_forecast + adjusted_safety)

    # Calculate order needed
    order_needed = max(0, order_up_to - inventory_position)

    # Apply threshold-based smoothing
    if order_needed > demand_forecast * threshold_factor:
        smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = order_needed

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
