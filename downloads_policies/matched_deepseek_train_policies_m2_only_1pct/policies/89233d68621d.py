# policy_hash: 89233d68621d089e94b730ca69d03ad1dd8c12c375e1ef0dd9e35f850f106f5b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 11569.76
# best_prompt_performance: 11569.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_084851.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 350.0  # OPT_PARAM: {"initial": 350.0, "min": 100, "max": 800, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.9, "type": "float"}
    order_smoothing = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from pipeline arrivals (arriving soon indicates recent demand)
    if len(pipeline_orders) > 0:
        # Weight recent arrivals more heavily
        weights = [0.1, 0.2, 0.3, 0.4]  # OPT_PARAM: {"initial": [0.1, 0.2, 0.3, 0.4], "min": [0.01, 0.01, 0.01, 0.01], "max": [1.0, 1.0, 1.0, 1.0], "type": "list"}
        weighted_sum = sum(w * p for w, p in zip(weights, pipeline_orders))
        demand_estimate = weighted_sum * demand_smoothing
    else:
        demand_estimate = 0

    # Dynamic base stock level
    dynamic_base = base_stock + safety_stock + demand_estimate

    # Calculate order amount
    order_amount = max(0, dynamic_base - inventory_position)

    # Smooth with recent orders to avoid volatility
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-2:] if len(pipeline_orders) >= 2 else pipeline_orders
        recent_avg = sum(recent_orders) / len(recent_orders)
        order_amount = order_smoothing * order_amount + (1 - order_smoothing) * recent_avg

    # Ensure integer order amount
    order_amount = int(round(order_amount))

    return order_amount
