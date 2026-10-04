# policy_hash: f1d4e75baa08690f88f6a3cc8d9f9337f5c3fb92673eb4dffbb88c5581928b34
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 16
# source_prompt_files: 2
# best_target_performance: 715.82
# best_prompt_performance: 715.82
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223906.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 251.5069614674628  # OPT_PARAM: {"initial": 251.5069614674628, "min": 200, "max": 350, "type": "float"}
    safety_stock = 12.538536715743314  # OPT_PARAM: {"initial": 12.538536715743314, "min": 10, "max": 60, "type": "float"}
    demand_forecast = 96.73103029756227  # OPT_PARAM: {"initial": 96.73103029756227, "min": 90, "max": 110, "type": "float"}
    lead_time_factor = 1.4856653997166829  # OPT_PARAM: {"initial": 1.4856653997166829, "min": 0.8, "max": 1.5, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate order-up-to level with lead-time adjusted safety stock
    order_up_to = base_stock + safety_stock * lead_time_factor

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with demand forecast adjustment
    if raw_order > 0:
        # Blend between base order and demand forecast
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
