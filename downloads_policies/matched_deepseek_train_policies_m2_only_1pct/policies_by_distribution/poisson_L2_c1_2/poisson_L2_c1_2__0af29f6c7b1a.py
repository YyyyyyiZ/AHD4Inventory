# policy_hash: 0af29f6c7b1a55f3ea85817a01e6cbf7cedd4de75c6cb90ea409220800bb1b82
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 1013.8
# best_prompt_performance: 1009.34
# best_rel_error_pct: 0.439929
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_062517.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 283.8867728599121  # OPT_PARAM: {"initial": 283.8867728599121, "min": 250, "max": 320, "type": "float"}
    safety_stock = 8.164528507984013  # OPT_PARAM: {"initial": 8.164528507984013, "min": 5, "max": 20, "type": "float"}
    demand_smoothing_factor = 0.21625257795461075  # OPT_PARAM: {"initial": 0.21625257795461075, "min": 0.1, "max": 0.35, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.5, "max": 0.9, "type": "float"}
    adjustment_factor = 0.7949681490910773  # OPT_PARAM: {"initial": 0.7949681490910773, "min": 0.7, "max": 1.0, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of pipeline orders
    if len(pipeline_orders) > 0:
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders))]
        total_weight = sum(weights)
        demand_estimate = sum(p * w for p, w in zip(pipeline_orders, weights)) / total_weight
        demand_estimate *= demand_smoothing_factor
    else:
        demand_estimate = 100.0 * demand_smoothing_factor

    # Dynamic base stock adjustment
    dynamic_base_stock = base_stock + safety_stock + demand_estimate

    # Calculate order amount
    order_amount = max(0, dynamic_base_stock - net_inventory)

    # Apply smoother adjustment
    order_amount = order_amount * adjustment_factor

    # Apply integer rounding
    order_amount = int(round(order_amount))

    return order_amount
