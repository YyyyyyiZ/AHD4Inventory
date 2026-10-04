# policy_hash: 60598423374321693da2f62394107ea023aa99468b979d272f0fd75cddbd2eb8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 31
# source_prompt_files: 1
# best_target_performance: 10791.44
# best_prompt_performance: 10791.65
# best_rel_error_pct: 0.001946
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_032153.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 302.80752628351814  # OPT_PARAM: {"initial": 302.80752628351814, "min": 200, "max": 600, "type": "float"}
    safety_stock = 22.807526283514125  # OPT_PARAM: {"initial": 22.807526283514125, "min": 10, "max": 100, "type": "float"}
    pipeline_weight = 0.011739523609825091  # OPT_PARAM: {"initial": 0.011739523609825091, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple base-stock policy with pipeline consideration
    target = base_stock + safety_stock

    # Reduce order when pipeline is large relative to target
    if target > 0:
        pipeline_ratio = sum(pipeline_orders) / target
        pipeline_adjustment = max(0.5, 1.0 - pipeline_weight * pipeline_ratio)
        target = target * pipeline_adjustment

    # Calculate order amount
    order_amount = max(0, target - inventory_position)

    # Round to integer
    return order_amount
