# policy_hash: 1e2ab33ad1f2ddb3e2a0d6fd46f247dbe0319dccf25430cfcd4f62960e0e749c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 1248.18
# best_prompt_performance: 1248.18
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_072747.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 341.83927638497954  # OPT_PARAM: {"initial": 341.83927638497954, "min": 250, "max": 380, "type": "float"}
    safety_stock = 66.83927638498427  # OPT_PARAM: {"initial": 66.83927638498427, "min": 20, "max": 80, "type": "float"}
    demand_adjustment = 1.02  # OPT_PARAM: {"initial": 1.02, "min": 0.9, "max": 1.15, "type": "float"}
    pipeline_weight = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.5, "max": 1.0, "type": "float"}
    order_smoothing = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 0.7, "type": "float"}
    demand_floor = 85.0  # OPT_PARAM: {"initial": 85.0, "min": 70.0, "max": 110.0, "type": "float"}
    demand_ceiling = 125.0  # OPT_PARAM: {"initial": 125.0, "min": 110.0, "max": 150.0, "type": "float"}
    inventory_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.3, "type": "float"}
    lost_sales_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent pipeline orders
    if len(pipeline_orders) >= 2:
        weights = [pipeline_weight, 1.0 - pipeline_weight]
        recent_orders = pipeline_orders[-2:]
        weighted_avg = sum(w * o for w, o in zip(weights, recent_orders)) / sum(weights)
        demand_estimate = weighted_avg * demand_adjustment
        demand_estimate = max(demand_floor, min(demand_ceiling, demand_estimate))
    else:
        demand_estimate = 100.0

    # Calculate target inventory with lost-sales adjustment
    # When on-hand inventory is low, increase target to prevent future stockouts
    inventory_shortage = max(0, demand_estimate - on_hand_inventory)
    lost_sales_adjustment = lost_sales_weight * inventory_shortage

    # Original inventory adjustment for excess inventory
    excess_inventory = max(0, on_hand_inventory - demand_estimate)
    inventory_adjustment = inventory_weight * excess_inventory

    # Combined target calculation
    target_inventory = base_stock + safety_stock - demand_estimate - inventory_adjustment + lost_sales_adjustment

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = order_smoothing * last_order + (1 - order_smoothing) * raw_order
    else:
        smoothed_order = raw_order

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
