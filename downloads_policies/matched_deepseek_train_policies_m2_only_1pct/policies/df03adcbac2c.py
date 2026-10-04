# policy_hash: df03adcbac2cab14cc344989fb28ff62d67d9e7e38337a7ff217b9bfeaa863ca
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 717.3
# best_prompt_performance: 717.3
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223505.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 284.8615171354885  # OPT_PARAM: {"initial": 284.8615171354885, "min": 100, "max": 400, "type": "float"}
    safety_stock = 45.0  # OPT_PARAM: {"initial": 45.0, "min": 0, "max": 100, "type": "float"}
    demand_forecast = 96.10828960588974  # OPT_PARAM: {"initial": 96.10828960588974, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.03562575636455164  # OPT_PARAM: {"initial": 0.03562575636455164, "min": 0.0, "max": 1.0, "type": "float"}
    lead_time_factor = 1.3  # OPT_PARAM: {"initial": 1.3, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust safety stock based on lead time
    adjusted_safety = safety_stock * lead_time_factor

    # Calculate order-up-to level
    order_up_to = max(base_stock, demand_forecast + adjusted_safety)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing only when order is non-zero
    if raw_order > 0:
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
