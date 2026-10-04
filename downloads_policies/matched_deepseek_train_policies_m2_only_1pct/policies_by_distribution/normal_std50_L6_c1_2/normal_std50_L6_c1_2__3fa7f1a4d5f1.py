# policy_hash: 3fa7f1a4d5f14eac45e2338d6e0a098c5e16ff69302428304ec4ec5cc1588fc0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 5600.96
# best_prompt_performance: 5602.28
# best_rel_error_pct: 0.023567
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_232632.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 509.7263389305685  # OPT_PARAM: {"initial": 509.7263389305685, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 45.030755477255234  # OPT_PARAM: {"initial": 45.030755477255234, "min": 0, "max": 200, "type": "float"}
    pipeline_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline composition
    # Give more weight to near-term arrivals
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = 1.0 - (i / (len(pipeline_orders) * 1.5))  # Decreasing weight for later arrivals
        weighted_pipeline += order * weight

    # Modified order-up-to level with safety stock adjustment
    adjusted_base = base_stock + safety_stock * (1 - weighted_pipeline / (base_stock + 1e-6))

    # Calculate order amount with pipeline factor
    order_amount = max(0, adjusted_base - on_hand_inventory - pipeline_factor * sum(pipeline_orders))

    # Round to nearest integer since order amount should be integer
    return order_amount
