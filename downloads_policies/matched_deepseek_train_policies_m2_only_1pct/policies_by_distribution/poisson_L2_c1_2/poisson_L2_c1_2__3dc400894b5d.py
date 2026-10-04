# policy_hash: 3dc400894b5db20adef91ef49f2edd2464fc002f46b78a5c05e3620d17772d0a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 1053.8
# best_prompt_performance: 1053.8
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_061725.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 271.8291761194849  # OPT_PARAM: {"initial": 271.8291761194849, "min": 100, "max": 400, "type": "float"}
    safety_stock = 12.772141158963404  # OPT_PARAM: {"initial": 12.772141158963404, "min": 0, "max": 50, "type": "float"}
    demand_smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of pipeline orders
    # More recent orders get higher weight
    if len(pipeline_orders) > 0:
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders))]
        weights = [w / sum(weights) for w in weights]
        demand_estimate = sum(p * w for p, w in zip(pipeline_orders, weights))
        demand_estimate *= demand_smoothing_factor
    else:
        demand_estimate = 100.0 * demand_smoothing_factor

    # Dynamic base stock adjustment
    dynamic_base_stock = base_stock + safety_stock + demand_estimate

    # Calculate order amount with smoother adjustment
    order_amount = max(0, dynamic_base_stock - net_inventory)

    # Apply integer rounding
    order_amount = int(round(order_amount))

    return order_amount
