# policy_hash: 6c1e3b24d091afc5ce5d976597f3301ebe04f3da4a2203571c31677647c8c3e3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 10249.0
# best_prompt_performance: 10249.0
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_072530.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 326.2441975361533  # OPT_PARAM: {"initial": 326.2441975361533, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 51.41294753616558  # OPT_PARAM: {"initial": 51.41294753616558, "min": 0, "max": 200, "type": "float"}
    adjustment_factor = 0.5029810812465318  # OPT_PARAM: {"initial": 0.5029810812465318, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = base_stock + safety_stock

    # Calculate order amount with adjustment factor
    order_amount = max(0, (target_inventory - inventory_position) * adjustment_factor)

    # Round to nearest integer since order amount should be integer
    order_amount = int(round(order_amount))

    return order_amount
