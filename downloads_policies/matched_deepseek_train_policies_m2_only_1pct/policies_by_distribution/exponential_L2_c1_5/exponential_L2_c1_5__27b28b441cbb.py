# policy_hash: 27b28b441cbbd7b5cbea81fa0dc94fd9d8ade36b7d321662eb4bdd527c922518
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 10166.1
# best_prompt_performance: 10166.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_232213.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 431.73758454082866  # OPT_PARAM: {"initial": 431.73758454082866, "min": 100, "max": 800, "type": "float"}
    safety_stock = 61.737584540823576  # OPT_PARAM: {"initial": 61.737584540823576, "min": 20, "max": 200, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple base-stock policy with smoothing
    target = base_stock + safety_stock
    order_amount = max(0, target - inventory_position)

    # Apply smoothing to avoid extreme fluctuations
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount

    # Round to nearest integer
    return order_amount
