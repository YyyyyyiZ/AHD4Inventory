# policy_hash: 246735491c4032c483356dedc882ca67005b3244ccdf67d4123bf3280b762a00
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2049.2
# best_prompt_performance: 2044.46
# best_rel_error_pct: 0.231310
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260127_230936.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 670.520182413  # OPT_PARAM: {"initial": 670.520182413, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 27.51991001337033  # OPT_PARAM: {"initial": 27.51991001337033, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = base_stock + safety_stock

    # Smooth ordering to avoid large fluctuations
    order_needed = max(0, target_inventory - inventory_position)
    order_amount = smoothing_factor * order_needed + (1 - smoothing_factor) * pipeline_orders[0] if pipeline_orders else order_needed

    # Round to nearest integer (as required by output type)
    return order_amount
