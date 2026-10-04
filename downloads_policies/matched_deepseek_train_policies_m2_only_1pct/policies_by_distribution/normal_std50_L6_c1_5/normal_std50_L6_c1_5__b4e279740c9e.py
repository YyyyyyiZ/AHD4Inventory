# policy_hash: b4e279740c9e82ee9bdc0e2652e170f41c3ff6a1d527e5de51e0fcb0b72647c7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 49
# source_prompt_files: 1
# best_target_performance: 6171.63
# best_prompt_performance: 6171.63
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_140925.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 739.8809035845743  # OPT_PARAM: {"initial": 739.8809035845743, "min": 700, "max": 900, "type": "float"}
    safety_stock = 107.5691336304687  # OPT_PARAM: {"initial": 107.5691336304687, "min": 100, "max": 200, "type": "float"}
    smoothing_factor = 0.15  # OPT_PARAM: {"initial": 0.15, "min": 0.15, "max": 0.4, "type": "float"}
    min_order = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 10, "max": 40, "type": "float"}
    low_inventory_threshold = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.5, "max": 0.85, "type": "float"}
    demand_anticipation_factor = 1.4551513644364837  # OPT_PARAM: {"initial": 1.4551513644364837, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on incoming pipeline (demand anticipation)
    pipeline_sum = sum(pipeline_orders)
    adjusted_base = base_stock * (1 + (pipeline_sum / (base_stock * demand_anticipation_factor)))

    # Calculate desired order-up-to level
    desired_level = adjusted_base + safety_stock

    # Calculate raw order amount
    raw_order = max(0, desired_level - inventory_position)

    # Apply smoothing
    smoothed_order = smoothing_factor * raw_order

    # Ensure minimum order quantity when inventory is low
    if inventory_position < desired_level * low_inventory_threshold:
        order_amount = max(min_order, smoothed_order)
    else:
        order_amount = smoothed_order

    return order_amount
