# policy_hash: 0627c6dcd5da513d3c0974d3ef4204f239ce00066820f072cb93bdfa19c578d1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 20
# source_prompt_files: 1
# best_target_performance: 11305.06
# best_prompt_performance: 11305.06
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_085057.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 286.2002418718735  # OPT_PARAM: {"initial": 286.2002418718735, "min": 100, "max": 600, "type": "float"}
    safety_stock = 126.20024187187543  # OPT_PARAM: {"initial": 126.20024187187543, "min": 50, "max": 300, "type": "float"}
    demand_alpha = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    order_alpha = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent pipeline arrivals (simpler approach)
    if len(pipeline_orders) > 0:
        # Use only the most recent pipeline order as demand indicator
        recent_demand_indicator = pipeline_orders[-1] if pipeline_orders[-1] > 0 else 0
        demand_estimate = recent_demand_indicator * demand_alpha
    else:
        demand_estimate = 0

    # Dynamic target inventory level
    target_inventory = base_stock + safety_stock + demand_estimate

    # Calculate base order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing with previous order to reduce volatility
    if len(pipeline_orders) > 0:
        previous_order = pipeline_orders[-1]
        order_amount = order_alpha * order_amount + (1 - order_alpha) * previous_order

    # Ensure integer order amount
    order_amount = int(round(order_amount))

    return order_amount
