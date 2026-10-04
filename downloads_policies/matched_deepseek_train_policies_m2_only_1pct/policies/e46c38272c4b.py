# policy_hash: e46c38272c4bb9ec30876b94d1e15aeb799ebdac8ef218b88d1c119b0f89a129
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_5
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 5036.14
# best_prompt_performance: 5036.14
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_115809.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 692.0049957614882  # OPT_PARAM: {"initial": 692.0049957614882, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 150.1  # OPT_PARAM: {"initial": 150.1, "min": 0, "max": 300, "type": "float"}
    smoothing_factor = 0.2999999999999999  # OPT_PARAM: {"initial": 0.2999999999999999, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate desired order-up-to level with safety stock
    desired_level = base_stock + safety_stock

    # Smooth ordering to avoid large fluctuations
    order_amount = max(0, smoothing_factor * (desired_level - inventory_position))

    # Round to nearest integer since order amounts should be integers
    return order_amount
