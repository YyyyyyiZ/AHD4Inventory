# policy_hash: caef40eaa98ea8005b72f99c3f206a8830f11c55579f32ad124c81780433492f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1038.74
# best_prompt_performance: 1038.7
# best_rel_error_pct: 0.003851
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_021923.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 302.3983878159247  # OPT_PARAM: {"initial": 302.3983878159247, "min": 200, "max": 400, "type": "float"}
    safety_stock = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 0, "max": 50, "type": "float"}
    demand_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    lead_time_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 2.0, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    # Use weighted average of pipeline orders as demand estimate
    if pipeline_orders:
        # Give more weight to recent orders
        weights = [0.4, 0.6] if len(pipeline_orders) >= 2 else [1.0]
        weighted_sum = sum(w * p for w, p in zip(weights, pipeline_orders[:len(weights)]))
        avg_weight = sum(weights[:len(pipeline_orders)])
        estimated_demand = weighted_sum / avg_weight if avg_weight > 0 else 100.0
    else:
        estimated_demand = 100.0

    # Adjust base stock based on lead time demand
    lead_time_demand = estimated_demand * lead_time_factor
    adjusted_base_stock = base_stock + demand_smoothing * (lead_time_demand - 100)

    # Ensure minimum safety stock
    target_inventory = max(adjusted_base_stock, safety_stock * 3)

    # Calculate order amount
    order_amount = max(0, target_inventory - net_inventory)

    # Apply practical ordering constraints
    if order_amount > 0:
        # Round to nearest 5 units for practicality
        order_amount = int(round(order_amount / 5) * 5)

    return order_amount
