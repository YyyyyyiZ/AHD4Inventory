# policy_hash: 1e5017a100e47247cf41f78be146c73904bc0c0fccc2d6bba6037cbbf229fcf6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1238.62
# best_prompt_performance: 1238.62
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_071859.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 356.42111045026314  # OPT_PARAM: {"initial": 356.42111045026314, "min": 280, "max": 380, "type": "float"}
    safety_stock = 50.51306924364663  # OPT_PARAM: {"initial": 50.51306924364663, "min": 30, "max": 70, "type": "float"}
    demand_adjustment = 1.05  # OPT_PARAM: {"initial": 1.05, "min": 0.95, "max": 1.15, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    order_smoothing = 0.6668277271966192  # OPT_PARAM: {"initial": 0.6668277271966192, "min": 0.3, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent pipeline orders
    if len(pipeline_orders) >= 2:
        weights = [pipeline_weight, 1.0 - pipeline_weight]
        recent_orders = pipeline_orders[-2:]
        weighted_avg = sum(w * o for w, o in zip(weights, recent_orders)) / sum(weights)
        demand_estimate = weighted_avg * demand_adjustment
    else:
        demand_estimate = 100.0

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock - demand_estimate

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = order_smoothing * last_order + (1 - order_smoothing) * raw_order
    else:
        smoothed_order = raw_order

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
