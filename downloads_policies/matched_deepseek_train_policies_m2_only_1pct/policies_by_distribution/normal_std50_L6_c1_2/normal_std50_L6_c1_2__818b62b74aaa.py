# policy_hash: 818b62b74aaa6fb447a7b6e86594243af1503a356ce0fe5ada04183f80d900e1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 5516.93
# best_prompt_performance: 5516.93
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_010937.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 494.05902346917037  # OPT_PARAM: {"initial": 494.05902346917037, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 30.413596333768492  # OPT_PARAM: {"initial": 30.413596333768492, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 1.0286605008278715  # OPT_PARAM: {"initial": 1.0286605008278715, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective pipeline inventory with weighting
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Order up to base_stock + safety_stock, adjusted by pipeline weighting
    order_amount = max(0, base_stock + safety_stock - inventory_position)

    # Round to nearest integer since order amounts should be integers
    return order_amount
