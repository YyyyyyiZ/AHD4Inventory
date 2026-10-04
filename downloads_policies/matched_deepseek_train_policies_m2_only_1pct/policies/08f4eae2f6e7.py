# policy_hash: 08f4eae2f6e7b760dfdc817d561f2f26d8b05b6571872bc35749c2212075d692
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 5185.78
# best_prompt_performance: 5186.18
# best_rel_error_pct: 0.007713
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_233319.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 536.4922822182357  # OPT_PARAM: {"initial": 536.4922822182357, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 52.540112076276195  # OPT_PARAM: {"initial": 52.540112076276195, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 1.062846874104964  # OPT_PARAM: {"initial": 1.062846874104964, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective pipeline inventory with weighting
    weighted_pipeline = sum(pipeline_orders[i] * (pipeline_weight ** i) for i in range(len(pipeline_orders)))

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - on_hand_inventory - weighted_pipeline)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.7845549671248973  # OPT_PARAM: {"initial": 0.7845549671248973, "min": 0.3, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
