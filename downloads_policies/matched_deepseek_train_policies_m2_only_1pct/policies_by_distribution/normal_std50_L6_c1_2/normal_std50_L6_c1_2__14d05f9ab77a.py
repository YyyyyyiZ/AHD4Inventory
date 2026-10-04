# policy_hash: 14d05f9ab77a261240e9f9618a8bdaadfce844f49f335941bd5445325f26d4c2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 4656.26
# best_prompt_performance: 4656.26
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_021723.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 534.5872259565015  # OPT_PARAM: {"initial": 534.5872259565015, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.63505581454138  # OPT_PARAM: {"initial": 50.63505581454138, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.38243020389396054  # OPT_PARAM: {"initial": 0.38243020389396054, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate smoothed base stock adjustment
    target_inventory = base_stock + safety_stock
    smoothed_target = smoothing_factor * target_inventory + (1 - smoothing_factor) * inventory_position

    # Calculate order amount with smoothing
    order_amount = max(0, smoothed_target - inventory_position)

    # Round to nearest integer since order amount should be integer
    return order_amount
