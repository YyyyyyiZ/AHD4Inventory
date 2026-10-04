# policy_hash: 3f235494706b3366859067b85a8c084e698511c9a9a58cc03a32e0241daed2bb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 11909.22
# best_prompt_performance: 11909.22
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_020255.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 460.79999999260747  # OPT_PARAM: {"initial": 460.79999999260747, "min": 300, "max": 700, "type": "float"}
    safety_stock = 100.79999999260201  # OPT_PARAM: {"initial": 100.79999999260201, "min": 50, "max": 200, "type": "float"}
    demand_estimate = 105.79999999260201  # OPT_PARAM: {"initial": 105.79999999260201, "min": 80, "max": 180, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    adjustment_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.9, "type": "float"}

    # Calculate weighted pipeline inventory
    weighted_pipeline = sum(p * (pipeline_weight ** i)
                           for i, p in enumerate(pipeline_orders))

    # Calculate target inventory level
    target = base_stock + safety_stock + demand_estimate

    # Calculate net inventory position
    net_inventory = on_hand_inventory + weighted_pipeline

    # Calculate order amount with adjustment
    raw_order = max(0, target - net_inventory)
    order_amount = int(round(raw_order * adjustment_factor))

    return order_amount
