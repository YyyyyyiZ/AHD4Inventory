# policy_hash: aa388bffe93b937336428b9199041c08bf4f306c6fe4aed7406e279a48e4430f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 32
# source_prompt_files: 2
# best_target_performance: 5960.47
# best_prompt_performance: 5959.27
# best_rel_error_pct: 0.020133
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_104523.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 296.05337856239913  # OPT_PARAM: {"initial": 296.05337856239913, "min": 150, "max": 450, "type": "float"}
    safety_stock = 26.34072127968114  # OPT_PARAM: {"initial": 26.34072127968114, "min": 20, "max": 150, "type": "float"}
    demand_adj_factor = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.4, "max": 1.3, "type": "float"}
    smoothing_factor = 0.22897450690261048  # OPT_PARAM: {"initial": 0.22897450690261048, "min": 0.1, "max": 1.0, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted pipeline information
    if len(pipeline_orders) >= 2:
        # Weight recent orders more heavily
        recent_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 0.9, "type": "float"}
        if len(pipeline_orders) >= 3:
            weights = [recent_weight, 0.2, 0.1]
            weighted_sum = sum(w * o for w, o in zip(weights, pipeline_orders[-3:]))
            demand_estimate = weighted_sum * demand_adj_factor
        else:
            recent_orders = pipeline_orders[-2:]
            demand_estimate = sum(recent_orders) / len(recent_orders) * demand_adj_factor
    else:
        demand_estimate = 0

    # Adjust base stock based on pipeline and demand estimate
    pipeline_effect = sum(pipeline_orders) * pipeline_weight
    dynamic_base = base_stock + max(0, safety_stock - demand_estimate) - pipeline_effect

    # Calculate raw order with smoothing
    raw_order = max(0, dynamic_base - inventory_position)

    # Apply exponential smoothing to reduce order volatility
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * max(pipeline_orders[-1:], default=0)

    # Round to nearest integer for practical ordering
    order_amount = int(round(smoothed_order))

    return order_amount
