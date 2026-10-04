# policy_hash: 3ec3064a1e380c442a9fc5065c9297fab03bd08f74e572f3f1f0b938d2c39495
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 30
# source_prompt_files: 2
# best_target_performance: 1384.38
# best_prompt_performance: 1384.38
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_065707.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 342.4823994796046  # OPT_PARAM: {"initial": 342.4823994796046, "min": 200, "max": 400, "type": "float"}
    safety_stock = 62.48239947961048  # OPT_PARAM: {"initial": 62.48239947961048, "min": 0, "max": 100, "type": "float"}
    demand_adjustment = 1.05  # OPT_PARAM: {"initial": 1.05, "min": 0.8, "max": 1.3, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 1.0, "type": "float"}
    order_smoothing = 0.6970402433118931  # OPT_PARAM: {"initial": 0.6970402433118931, "min": 0.0, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent pipeline orders
    # Pipeline orders reflect actual orders placed, which correlate with demand
    if len(pipeline_orders) >= 2:
        # Give more weight to recent orders
        weights = [pipeline_weight, 1.0 - pipeline_weight]
        recent_orders = pipeline_orders[-2:]
        weighted_avg = sum(w * o for w, o in zip(weights, recent_orders)) / sum(weights)
        demand_estimate = weighted_avg * demand_adjustment
    else:
        demand_estimate = 100.0  # Default estimate

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
