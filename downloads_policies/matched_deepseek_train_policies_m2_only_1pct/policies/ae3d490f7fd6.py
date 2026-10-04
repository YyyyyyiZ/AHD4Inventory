# policy_hash: ae3d490f7fd6ef4554734c98f63ec0c524d7afdf5353f3bad892b51db3387c2f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 38
# source_prompt_files: 1
# best_target_performance: 6173.76
# best_prompt_performance: 6173.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_081701.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 300.0  # OPT_PARAM: {"initial": 300.0, "min": 150, "max": 300, "type": "float"}
    safety_stock = 35.0  # OPT_PARAM: {"initial": 35.0, "min": 20, "max": 60, "type": "float"}
    demand_forecast_factor = 1.05  # OPT_PARAM: {"initial": 1.05, "min": 0.8, "max": 1.3, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.3, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted average of recent pipeline orders
    if len(pipeline_orders) > 0:
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders))]
        weighted_sum = sum(w * q for w, q in zip(weights, pipeline_orders))
        total_weight = sum(weights)
        demand_estimate = (weighted_sum / total_weight) * demand_forecast_factor
    else:
        demand_estimate = 0

    # Simple order-up-to level with safety stock
    order_up_to = max(base_stock, safety_stock + demand_estimate)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with previous order
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
