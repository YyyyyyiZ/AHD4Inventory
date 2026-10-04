# policy_hash: e158f83d201163bdc1dab63f5b5df8e5b3e349d5f4b79eab65da8df05ce37fe6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 851.1
# best_prompt_performance: 847.3
# best_rel_error_pct: 0.446481
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_052557.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 704.9063054024732  # OPT_PARAM: {"initial": 704.9063054024732, "min": 500, "max": 800, "type": "float"}
    safety_stock = 105.29173196845665  # OPT_PARAM: {"initial": 105.29173196845665, "min": 50, "max": 120, "type": "float"}
    demand_estimate = 110.0  # OPT_PARAM: {"initial": 110.0, "min": 90, "max": 110, "type": "float"}
    max_order = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 150, "type": "float"}
    min_order = 19.9  # OPT_PARAM: {"initial": 19.9, "min": 0, "max": 20, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with smoothing
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Adjust target based on pipeline composition
    pipeline_variance = sum((q - demand_estimate) ** 2 for q in pipeline_orders) / max(1, len(pipeline_orders))
    pipeline_adjustment = max(0, pipeline_variance ** 0.5) * 0.5

    # Calculate target inventory position with dynamic adjustment
    target_position = expected_demand_during_leadtime + safety_stock + pipeline_adjustment

    # Calculate order amount with smoothing
    raw_order = target_position - inventory_position
    order_amount = max(0, raw_order)

    # Apply smoothing to avoid large order swings
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Apply base stock level as upper bound
    if inventory_position + order_amount > base_stock:
        order_amount = max(0, base_stock - inventory_position)

    # Apply bounds
    order_amount = min(order_amount, max_order)
    order_amount = max(order_amount, min_order)

    return order_amount
