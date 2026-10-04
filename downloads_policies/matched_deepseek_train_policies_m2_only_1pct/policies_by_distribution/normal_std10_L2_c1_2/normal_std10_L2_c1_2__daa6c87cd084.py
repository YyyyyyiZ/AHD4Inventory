# policy_hash: daa6c87cd084d7b8ddc9ec698a3334a1a5b91040386342489d6881e21d0f9df7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 893.24
# best_prompt_performance: 893.24
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_052602.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 323.2409795974007  # OPT_PARAM: {"initial": 323.2409795974007, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 77.34088744472967  # OPT_PARAM: {"initial": 77.34088744472967, "min": 0, "max": 200, "type": "float"}
    adjustment_factor = 0.4677352227521778  # OPT_PARAM: {"initial": 0.4677352227521778, "min": 0.1, "max": 1.5, "type": "float"}

    inventory_position = on_hand_inventory + sum(pipeline_orders)
    target_level = base_stock + safety_stock

    # Smooth adjustment to avoid large order fluctuations
    order_amount = max(0, (target_level - inventory_position) * adjustment_factor)

    # Round to nearest integer for practical ordering
    return order_amount
