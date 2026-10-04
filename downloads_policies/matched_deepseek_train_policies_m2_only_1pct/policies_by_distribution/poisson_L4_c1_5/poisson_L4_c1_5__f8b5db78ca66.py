# policy_hash: f8b5db78ca66e6649d6af31f70d82846730b9c024ac5fc65bf6868001cda7aad
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2475.58
# best_prompt_performance: 2475.46
# best_rel_error_pct: 0.004847
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_081818.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 447.5771085855967  # OPT_PARAM: {"initial": 447.5771085855967, "min": 300, "max": 600, "type": "float"}
    safety_stock = 56.84592523868893  # OPT_PARAM: {"initial": 56.84592523868893, "min": 10, "max": 100, "type": "float"}
    demand_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    pipeline_weight = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.3, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted average of pipeline orders
    if len(pipeline_orders) > 0:
        # Weight recent orders more heavily
        weights = [pipeline_weight ** (len(pipeline_orders) - i - 1) for i in range(len(pipeline_orders))]
        weighted_sum = sum(w * q for w, q in zip(weights, pipeline_orders))
        weight_total = sum(weights)
        demand_estimate = weighted_sum / weight_total if weight_total > 0 else 100.0
    else:
        demand_estimate = 100.0

    # Smooth demand estimate to avoid overreaction
    smoothed_demand = 100.0 + (demand_estimate - 100.0) * demand_smoothing

    # Adjust base stock based on smoothed demand
    adjusted_base = base_stock * (smoothed_demand / 100.0)

    # Calculate target inventory position
    target_position = adjusted_base + safety_stock

    # Place order to reach target
    order_amount = max(0, target_position - inventory_position)

    # Round to nearest integer (orders should be integer quantities)
    order_amount = int(round(order_amount))

    return order_amount
