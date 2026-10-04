# policy_hash: 03a80d62ba103b470edb916b09e21e8b7bd26f7d06df7c7ef23f0fd0a065b6cb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 77
# source_prompt_files: 1
# best_target_performance: 1167.37
# best_prompt_performance: 1167.37
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_205317.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 595.2633250780286  # OPT_PARAM: {"initial": 595.2633250780286, "min": 450, "max": 650, "type": "float"}
    safety_stock = 28.64754800429029  # OPT_PARAM: {"initial": 28.64754800429029, "min": 0, "max": 40, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use recent pipeline orders for demand estimation
    if len(pipeline_orders) > 0:
        # Weight recent orders more heavily
        recent_weights = [0.1, 0.15, 0.25, 0.25, 0.15, 0.1]
        weights = recent_weights[:len(pipeline_orders)]
        # Normalize weights
        weight_sum = sum(weights)
        normalized_weights = [w/weight_sum for w in weights]
        estimated_demand = sum(p * w for p, w in zip(pipeline_orders, normalized_weights))
    else:
        estimated_demand = 100.0

    # Adjust base stock based on estimated demand
    demand_adjustment = 0.8671545514139554  # OPT_PARAM: {"initial": 0.8671545514139554, "min": 0.3, "max": 1.5, "type": "float"}
    adjusted_base = base_stock + estimated_demand * demand_adjustment

    # Calculate target inventory level
    target_inventory = adjusted_base + safety_stock

    # Order amount calculation
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing based on recent orders
    if len(pipeline_orders) > 0:
        recent_avg = sum(pipeline_orders[-3:]) / min(3, len(pipeline_orders))
        smoothing_factor = 0.8841769351933002  # OPT_PARAM: {"initial": 0.8841769351933002, "min": 0.3, "max": 1.0, "type": "float"}
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_avg

    # Order limits
    max_order = 99.1156066472005  # OPT_PARAM: {"initial": 99.1156066472005, "min": 80, "max": 200, "type": "float"}
    min_order = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 20, "type": "float"}

    # Additional constraint: avoid small orders when close to target
    buffer_zone = 25.0  # OPT_PARAM: {"initial": 25.0, "min": 10, "max": 50, "type": "float"}
    if abs(inventory_position - target_inventory) < buffer_zone:
        order_amount = min(order_amount, estimated_demand)

    order_amount = max(min_order, min(order_amount, max_order))

    return order_amount
