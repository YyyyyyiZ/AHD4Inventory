# policy_hash: 5ec04ddcf07c67c38a86ce9352c4b6d89bc3fc7bc237505da45638982ba72e82
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 2602.78
# best_prompt_performance: 2609.78
# best_rel_error_pct: 0.268943
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_165703.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 649.1770473985289  # OPT_PARAM: {"initial": 649.1770473985289, "min": 400, "max": 800, "type": "float"}
    safety_stock = 102.59113814408803  # OPT_PARAM: {"initial": 102.59113814408803, "min": 50, "max": 120, "type": "float"}
    smoothing_factor = 0.7112483558964999  # OPT_PARAM: {"initial": 0.7112483558964999, "min": 0.3, "max": 1.0, "type": "float"}
    demand_estimate_factor = 1.3379399876353133  # OPT_PARAM: {"initial": 1.3379399876353133, "min": 0.9, "max": 1.5, "type": "float"}
    min_order_threshold = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.3, "type": "float"}
    lead_time = 6

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent pipeline orders
    if len(pipeline_orders) > 0:
        # Use recent orders for demand estimation (last 3 periods)
        recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
        non_zero_orders = [q for q in recent_orders if q > 0]
        if len(non_zero_orders) > 0:
            avg_recent_demand = sum(non_zero_orders) / len(non_zero_orders)
        else:
            avg_recent_demand = 100.0
    else:
        avg_recent_demand = 100.0

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock * (demand_estimate_factor - 0.5)

    # Calculate required order
    required_order = max(0, target_inventory - inventory_position)

    # Apply smoothing
    smoothed_order = smoothing_factor * required_order

    # Only place order if significant enough
    if smoothed_order < avg_recent_demand * min_order_threshold:
        order_amount = 0
    else:
        order_amount = int(round(smoothed_order))

    return order_amount
