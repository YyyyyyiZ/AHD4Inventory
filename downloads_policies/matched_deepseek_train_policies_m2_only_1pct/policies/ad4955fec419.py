# policy_hash: ad4955fec4198a9d337b6c7cd60dd85a8bb49a48be2220f8632176b7299948bc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 978.14
# best_prompt_performance: 982.06
# best_rel_error_pct: 0.400761
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_235533.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.0721621193327  # OPT_PARAM: {"initial": 450.0721621193327, "min": 300, "max": 600, "type": "float"}
    demand_estimate = 99.83675236781507  # OPT_PARAM: {"initial": 99.83675236781507, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory position
    target_position = base_stock

    # Order up to target, but ensure non-negative
    order_amount = max(0, target_position - inventory_position)

    # Apply smoothing to avoid large fluctuations
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
