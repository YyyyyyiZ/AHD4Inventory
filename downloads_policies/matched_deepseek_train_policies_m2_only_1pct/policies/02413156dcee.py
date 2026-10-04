# policy_hash: 02413156dcee7cd98c78101e69e86a85cf0b3fcb76c2fcf25af7e78f4428c885
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2671.41
# best_prompt_performance: 2671.88
# best_rel_error_pct: 0.017594
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_165319.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 603.9085077431267  # OPT_PARAM: {"initial": 603.9085077431267, "min": 400, "max": 800, "type": "float"}
    safety_stock = 83.90850585126195  # OPT_PARAM: {"initial": 83.90850585126195, "min": 50, "max": 120, "type": "float"}
    smoothing_factor = 0.8086303188561962  # OPT_PARAM: {"initial": 0.8086303188561962, "min": 0.3, "max": 1.0, "type": "float"}
    demand_estimate_factor = 1.2551266192935369  # OPT_PARAM: {"initial": 1.2551266192935369, "min": 0.9, "max": 1.5, "type": "float"}
    min_order_threshold = 0.19133245027375967  # OPT_PARAM: {"initial": 0.19133245027375967, "min": 0.05, "max": 0.3, "type": "float"}
    lead_time = 6  # Fixed lead time

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent pipeline orders (excluding zeros during planning phase)
    if len(pipeline_orders) > 0:
        # Use all non-zero orders for demand estimation
        non_zero_orders = [q for q in pipeline_orders if q > 0]
        if len(non_zero_orders) > 0:
            avg_recent_demand = sum(non_zero_orders) / len(non_zero_orders)
        else:
            avg_recent_demand = 100.0  # Default estimate
    else:
        avg_recent_demand = 100.0

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock * demand_estimate_factor

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
