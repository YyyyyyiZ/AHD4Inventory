# policy_hash: ac2f232434f002b6c8e65659f4a09834ecfa246703a52034111018c729e14c4d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1271.04
# best_prompt_performance: 1270.86
# best_rel_error_pct: 0.014162
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_030012.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 477.94581688484215  # OPT_PARAM: {"initial": 477.94581688484215, "min": 400, "max": 550, "type": "float"}
    safety_factor = 1.1180766300019847  # OPT_PARAM: {"initial": 1.1180766300019847, "min": 0.8, "max": 2.0, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    lead_time_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    demand_adjustment = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.5, "type": "float"}

    # Calculate weighted pipeline with emphasis on near-term arrivals
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = lead_time_weight ** (len(pipeline_orders) - i - 1)
        weighted_pipeline += weight * order

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    effective_pipeline = pipeline_weight * weighted_pipeline

    # Adjust target based on pipeline coverage and demand adjustment
    adjusted_target = base_stock * demand_adjustment + safety_factor * (base_stock - effective_pipeline)

    # Calculate order needed
    order_needed = max(0, adjusted_target - inventory_position)

    # Apply smoothing to prevent overshooting
    smoothed_order = smoothing_factor * order_needed

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
