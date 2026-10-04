# policy_hash: ec02a8af62ec6b430cc92576bdf504f60e8a6174f04f316a1b1f772914e156ab
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 13681.02
# best_prompt_performance: 13681.02
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_095645.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 485.3586334799213  # OPT_PARAM: {"initial": 485.3586334799213, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 58.50873173943871  # OPT_PARAM: {"initial": 58.50873173943871, "min": 0, "max": 300, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate effective pipeline inventory with weighting
    weighted_pipeline = sum(pipeline_orders[i] * (pipeline_weight ** i) for i in range(len(pipeline_orders)))

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Order up to base_stock, but ensure at least safety_stock coverage
    target_inventory = max(base_stock, safety_stock + sum(pipeline_orders))

    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer since order amount must be integer
    return order_amount
