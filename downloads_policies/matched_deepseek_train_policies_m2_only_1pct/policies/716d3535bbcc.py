# policy_hash: 716d3535bbccf015c8b6348a1b76387458b2e290bc3be66e78dd7fb002d8dfc1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 838.94
# best_prompt_performance: 838.94
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_023758.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 320.0  # OPT_PARAM: {"initial": 320.0, "min": 200, "max": 500, "type": "float"}
    safety_stock = 237.03489370936822  # OPT_PARAM: {"initial": 237.03489370936822, "min": 100, "max": 250, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}
    lead_time_factor = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.0, "max": 1.5, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders) * lead_time_factor

    # Calculate target inventory level
    target_inventory = expected_demand_during_leadtime + safety_stock

    # Calculate base order amount
    base_order = max(0, target_inventory - net_inventory)

    # Apply smoothing: blend with previous pipeline order for stability
    if pipeline_orders:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * last_order + (1 - smoothing_factor) * base_order
    else:
        smoothed_order = base_order

    # Apply adjustment factor
    order_amount = smoothed_order * adjustment_factor

    # Apply base stock as upper bound with tighter control
    max_order = max(0, base_stock - net_inventory)
    order_amount = min(order_amount, max_order)

    # Ensure order amount is reasonable relative to expected demand
    min_order = max(0, demand_estimate - on_hand_inventory - pipeline_orders[0] if pipeline_orders else 0)
    order_amount = max(order_amount, min_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
