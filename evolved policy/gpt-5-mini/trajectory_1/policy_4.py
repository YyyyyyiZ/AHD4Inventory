def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Estimate of average demand per period (used to size lead-time coverage)
    mean_demand = 124.21215797244086  # OPT_PARAM: {"initial": 124.21215797244086, "min": 50.0, "max": 150.0, "type": "float"}
    # Factor to scale lead-time coverage (reduce to lower excessive holding)
    service_factor = 0.8094838077727992  # OPT_PARAM: {"initial": 0.8094838077727992, "min": 0.3, "max": 1.2, "type": "float"}
    # Small extra buffer in units of periods
    extra_periods = 1.5737876070638752  # OPT_PARAM: {"initial": 1.5737876070638752, "min": 0.0, "max": 3.0, "type": "float"}
    # Dampening factor to avoid aggressive full replenishment
    damping = 0.8035122899476465  # OPT_PARAM: {"initial": 0.8035122899476465, "min": 0.5, "max": 1.0, "type": "float"}
    # Bounds on a single-period order
    min_order = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 200.0, "type": "float"}
    max_order = 110.1  # OPT_PARAM: {"initial": 110.1, "min": 10.0, "max": 1000.0, "type": "float"}

    L = len(pipeline_orders)
    # inventory position = on-hand + on-order (including arriving now)
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Target inventory position: cover expected demand over lead time plus buffer
    target_ip = mean_demand * (service_factor * L + extra_periods)

    raw_order = (target_ip - inventory_position) * damping

    # Enforce bounds
    raw_order = max(min_order, raw_order)
    raw_order = min(max_order, raw_order)

    order_amount = int(max(0, round(raw_order)))
    return order_amount
