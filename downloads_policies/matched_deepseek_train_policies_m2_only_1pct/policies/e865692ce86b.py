# policy_hash: e865692ce86becb49f679387ab33ab9e461669e49d8293e41fd14e9e2c741268
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 2818.1
# best_prompt_performance: 2804.82
# best_rel_error_pct: 0.471239
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_004303.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 680.0  # OPT_PARAM: {"initial": 680.0, "min": 500, "max": 900, "type": "float"}
    safety_stock = 24.142743068232488  # OPT_PARAM: {"initial": 24.142743068232488, "min": 10, "max": 60, "type": "float"}
    smoothing_factor = 0.763922150638743  # OPT_PARAM: {"initial": 0.763922150638743, "min": 0.5, "max": 1.0, "type": "float"}
    avg_demand = 98.79050458170816  # OPT_PARAM: {"initial": 98.79050458170816, "min": 80, "max": 120, "type": "float"}
    pipeline_low_multiplier = 1.1748063087973506  # OPT_PARAM: {"initial": 1.1748063087973506, "min": 1.0, "max": 1.5, "type": "float"}
    pipeline_high_multiplier = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.6, "max": 1.0, "type": "float"}
    lead_time = 6

    inventory_position = on_hand_inventory + sum(pipeline_orders)
    lead_time_demand = avg_demand * lead_time
    target_inventory = lead_time_demand + safety_stock

    # Calculate pipeline coverage ratio
    pipeline_coverage = sum(pipeline_orders) / (lead_time_demand + 1e-6)

    # Dynamic adjustment based on pipeline coverage
    if pipeline_coverage < 0.9:
        target_inventory *= pipeline_low_multiplier
    elif pipeline_coverage > 1.1:
        target_inventory *= pipeline_high_multiplier

    # Calculate order amount with smoothing
    order_amount = smoothing_factor * (target_inventory - inventory_position)

    # Ensure non-negative order
    order_amount = max(0, order_amount)

    # Round to nearest integer
    return order_amount
