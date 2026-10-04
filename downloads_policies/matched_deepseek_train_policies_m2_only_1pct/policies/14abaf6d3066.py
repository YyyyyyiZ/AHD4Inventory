# policy_hash: 14abaf6d3066abd16a1815b68ae89671fd15378907650896e8401027ef540deb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1301.56
# best_prompt_performance: 1301.56
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_004813.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 419.002324386555  # OPT_PARAM: {"initial": 419.002324386555, "min": 380, "max": 480, "type": "float"}
    safety_stock = 39.1023243865548  # OPT_PARAM: {"initial": 39.1023243865548, "min": 20, "max": 60, "type": "float"}
    demand_forecast = 99.1697339135294  # OPT_PARAM: {"initial": 99.1697339135294, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate total pipeline
    total_pipeline = sum(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + total_pipeline

    # Order-up-to level with safety stock
    order_up_to = base_stock + safety_stock

    # Calculate order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
