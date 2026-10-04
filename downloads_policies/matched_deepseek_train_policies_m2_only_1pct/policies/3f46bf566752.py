# policy_hash: 3f46bf5667528bce4ba1929ad0cae74cea87c0a07ed57e5383f251e28e249f69
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 5539.58
# best_prompt_performance: 5539.58
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_010804.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 508.55217014018575  # OPT_PARAM: {"initial": 508.55217014018575, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 24.599999998220124  # OPT_PARAM: {"initial": 24.599999998220124, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate effective pipeline inventory with weighting
    effective_pipeline = pipeline_orders[0]  # Arriving this period
    for i in range(1, len(pipeline_orders)):
        effective_pipeline += pipeline_orders[i] * (pipeline_weight ** i)

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - on_hand_inventory - effective_pipeline)

    # Round to nearest integer since order amounts should be integers
    order_amount = int(round(order_amount))

    return order_amount
