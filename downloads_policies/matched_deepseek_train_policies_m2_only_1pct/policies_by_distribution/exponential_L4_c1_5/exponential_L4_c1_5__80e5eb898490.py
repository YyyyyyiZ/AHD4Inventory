# policy_hash: 80e5eb8984909339c772bc1a208a6d631ca79a448ac82cfada61682c97a98e6e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 10967.19
# best_prompt_performance: 10967.19
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_050356.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 441.72383127912866  # OPT_PARAM: {"initial": 441.72383127912866, "min": 300, "max": 800, "type": "float"}
    demand_estimate = 99.22745805583621  # OPT_PARAM: {"initial": 99.22745805583621, "min": 80, "max": 200, "type": "float"}
    smoothing_factor = 0.23302956152195511  # OPT_PARAM: {"initial": 0.23302956152195511, "min": 0.1, "max": 1.0, "type": "float"}
    buffer_multiplier = 0.33821148639931575  # OPT_PARAM: {"initial": 0.33821148639931575, "min": 0.1, "max": 1.5, "type": "float"}
    min_order_threshold = 0.7722652769292686  # OPT_PARAM: {"initial": 0.7722652769292686, "min": 0.3, "max": 0.9, "type": "float"}
    safety_stock_factor = 0.922868772635812  # OPT_PARAM: {"initial": 0.922868772635812, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate safety stock based on lead time demand variability
    safety_stock = safety_stock_factor * demand_estimate

    # Calculate target inventory position with safety stock
    target_position = base_stock + expected_lead_time_demand * buffer_multiplier + safety_stock

    # Calculate order needed to reach target
    order_needed = target_position - inventory_position

    # Apply smoothing and ensure non-negative order
    if order_needed > 0:
        # Smooth order adjustment
        order_amount = max(0, smoothing_factor * order_needed)
        # Order at least expected demand when significantly below target
        if inventory_position < target_position * min_order_threshold:
            order_amount = max(order_amount, demand_estimate * 0.8)
    else:
        order_amount = 0

    return order_amount
