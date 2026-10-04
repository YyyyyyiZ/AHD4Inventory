# policy_hash: 4a2957338f95e42e9e2a9a1d3cf8ec4f891b43785987a4d53a35adc663885d9f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 35
# source_prompt_files: 1
# best_target_performance: 1266.68
# best_prompt_performance: 1268.04
# best_rel_error_pct: 0.107367
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_072358.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 342.5514629152589  # OPT_PARAM: {"initial": 342.5514629152589, "min": 200, "max": 400, "type": "float"}
    safety_stock = 62.551462915264736  # OPT_PARAM: {"initial": 62.551462915264736, "min": 0, "max": 100, "type": "float"}
    demand_adjustment = 1.05  # OPT_PARAM: {"initial": 1.05, "min": 0.8, "max": 1.3, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 1.0, "type": "float"}
    order_smoothing = 0.6794160456553359  # OPT_PARAM: {"initial": 0.6794160456553359, "min": 0.0, "max": 0.8, "type": "float"}
    demand_floor = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 50.0, "max": 120.0, "type": "float"}
    demand_ceiling = 130.0  # OPT_PARAM: {"initial": 130.0, "min": 100.0, "max": 160.0, "type": "float"}
    inventory_weight = 0.28554501540368127  # OPT_PARAM: {"initial": 0.28554501540368127, "min": 0.0, "max": 0.5, "type": "float"}

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
        # Constrain demand estimate to reasonable bounds
        demand_estimate = max(demand_floor, min(demand_ceiling, demand_estimate))
    else:
        demand_estimate = 100.0  # Default estimate

    # Calculate target inventory level with dynamic adjustment
    # Reduce target when inventory is high to avoid overstocking
    excess_inventory = max(0, on_hand_inventory - demand_estimate)
    inventory_adjustment = inventory_weight * excess_inventory
    target_inventory = base_stock + safety_stock - demand_estimate - inventory_adjustment

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
