# policy_hash: aadd3eec0968ecbd756cbf90a0818810c4118af8fa6a48193ad15c3fbd006d97
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 698.56
# best_prompt_performance: 698.56
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_225040.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 291.6288128078759  # OPT_PARAM: {"initial": 291.6288128078759, "min": 250, "max": 350, "type": "float"}
    safety_stock = 38.2  # OPT_PARAM: {"initial": 38.2, "min": 20, "max": 60, "type": "float"}
    demand_forecast = 96.63252420283766  # OPT_PARAM: {"initial": 96.63252420283766, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    lead_time_factor = 1.25  # OPT_PARAM: {"initial": 1.25, "min": 0.8, "max": 1.5, "type": "float"}
    threshold_factor = 0.6899251456097207  # OPT_PARAM: {"initial": 0.6899251456097207, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust safety stock based on lead time
    adjusted_safety = safety_stock * lead_time_factor

    # Calculate order-up-to level
    order_up_to = max(base_stock, demand_forecast + adjusted_safety)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply threshold-based smoothing
    if raw_order > demand_forecast * threshold_factor:
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
