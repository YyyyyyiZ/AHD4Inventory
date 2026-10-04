# policy_hash: 0cab0a212bc92d7a217a1d9e7afddffd2e76a7b7cab3afa00a65bd56ed8316c4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 27
# source_prompt_files: 2
# best_target_performance: 1214.26
# best_prompt_performance: 1214.26
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_004305.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 449.43947877728493  # OPT_PARAM: {"initial": 449.43947877728493, "min": 300, "max": 600, "type": "float"}
    safety_stock = 39.4395455775477  # OPT_PARAM: {"initial": 39.4395455775477, "min": 0, "max": 100, "type": "float"}
    demand_forecast = 96.92657819525137  # OPT_PARAM: {"initial": 96.92657819525137, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.2, "type": "float"}
    pipeline_weight = 0.6367898921743645  # OPT_PARAM: {"initial": 0.6367898921743645, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Dynamic order-up-to level based on pipeline composition
    order_up_to = base_stock + safety_stock * (1 - pipeline_weight)

    # Order-up-to policy with smoothing
    raw_order = max(0, order_up_to - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
