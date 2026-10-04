# policy_hash: 052274b1eefcfe6fe619008da78542d78ebd0aaab4fb03067303ddcdd9935710
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 9
# source_prompt_files: 2
# best_target_performance: 970.28
# best_prompt_performance: 970.04
# best_rel_error_pct: 0.024735
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_064251.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 287.03499461077706  # OPT_PARAM: {"initial": 287.03499461077706, "min": 280, "max": 310, "type": "float"}
    safety_stock = 13.194367526303548  # OPT_PARAM: {"initial": 13.194367526303548, "min": 8, "max": 18, "type": "float"}
    demand_smoothing_factor = 0.15  # OPT_PARAM: {"initial": 0.15, "min": 0.15, "max": 0.25, "type": "float"}
    pipeline_weight = 0.65  # OPT_PARAM: {"initial": 0.65, "min": 0.55, "max": 0.75, "type": "float"}
    adjustment_factor = 0.75  # OPT_PARAM: {"initial": 0.75, "min": 0.75, "max": 0.95, "type": "float"}
    lost_sales_weight = 1.857030137910387  # OPT_PARAM: {"initial": 1.857030137910387, "min": 1.5, "max": 2.2, "type": "float"}

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

    # Dynamic base stock adjustment with cost-aware safety stock
    # Increase safety stock when lost sales are more costly (p > h)
    cost_aware_safety = safety_stock * lost_sales_weight

    dynamic_base_stock = base_stock + cost_aware_safety + demand_estimate

    # Calculate order amount with more aggressive replenishment
    order_amount = max(0, dynamic_base_stock - net_inventory)

    # Apply smoother adjustment
    order_amount = order_amount * adjustment_factor

    # Apply integer rounding
    order_amount = int(round(order_amount))

    return order_amount
