def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Estimate of average demand per period (used to size lead-time coverage)
    mean_demand = 120.91088498551726  # OPT_PARAM: {"initial": 120.91088498551726, "min": 50.0, "max": 150.0, "type": "float"}
    # Factor to scale lead-time coverage (reduce to lower excessive holding)
    service_factor = 0.8076733988233287  # OPT_PARAM: {"initial": 0.8076733988233287, "min": 0.3, "max": 1.2, "type": "float"}
    # Small extra buffer in units of periods (trimmed relative to historical)
    extra_periods = 1.6033962114928277  # OPT_PARAM: {"initial": 1.6033962114928277, "min": 0.0, "max": 3.0, "type": "float"}
    # Dampening factor to avoid aggressive full replenishment (reduces overstock)
    damping = 0.844108170984865  # OPT_PARAM: {"initial": 0.844108170984865, "min": 0.5, "max": 1.0, "type": "float"}
    # Bounds on a single-period order
    min_order = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 200.0, "type": "float"}
    max_order = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 10.0, "max": 1000.0, "type": "float"}

    L = len(pipeline_orders)
    # inventory position = on-hand + on-order (including arriving now)
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Target inventory position: cover expected demand over lead time plus a modest buffer
    target_ip = mean_demand * (service_factor * L + extra_periods)

    raw_order = target_ip - inventory_position
    # Apply dampening to avoid overshooting and reduce holding
    raw_order = raw_order * damping

    # Enforce bounds
    raw_order = max(min_order, raw_order)
    raw_order = min(max_order, raw_order)

    order_amount = int(max(0, round(raw_order)))
    return order_amount
