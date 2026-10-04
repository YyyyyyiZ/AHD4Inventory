# policy_hash: 4f5cacea49f36a82d4968621be44ef400fd7de956c3b03d6a323b65c4523f2a7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 4291.5
# best_prompt_performance: 4300.36
# best_rel_error_pct: 0.206455
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251219_115047.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 506.18253227458626  # OPT_PARAM: {"initial": 506.18253227458626, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 79.29983496194316  # OPT_PARAM: {"initial": 79.29983496194316, "min": 0, "max": 300, "type": "float"}
    smoothing_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = base_stock + safety_stock

    # Calculate order amount with smoothing to avoid extreme fluctuations
    raw_order = max(0, target_inventory - inventory_position)
    order_amount = int(round(smoothing_factor * raw_order + (1 - smoothing_factor) * pipeline_orders[-1] if pipeline_orders else raw_order))

    return order_amount
