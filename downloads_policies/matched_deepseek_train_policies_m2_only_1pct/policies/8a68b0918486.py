# policy_hash: 8a68b0918486eb8e61afe4c1ae298fbb9630cde5ea3ebff409f0d6109b07de50
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 82
# source_prompt_files: 1
# best_target_performance: 1303.16
# best_prompt_performance: 1303.04
# best_rel_error_pct: 0.009208
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_035511.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 308.00033524244304  # OPT_PARAM: {"initial": 308.00033524244304, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.00001724907757  # OPT_PARAM: {"initial": 50.00001724907757, "min": 0, "max": 200, "type": "float"}
    adjustment_factor = 0.650752984995027  # OPT_PARAM: {"initial": 0.650752984995027, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Base order-up-to level with safety stock
    target_level = base_stock + safety_stock

    # Calculate order amount with adjustment factor
    raw_order = max(0, target_level - inventory_position)
    order_amount = int(round(raw_order * adjustment_factor))

    return order_amount
