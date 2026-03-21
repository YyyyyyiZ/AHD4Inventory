def compute_order_amount(on_hand_inventory, pipeline_orders):
    mean_demand = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 50.0, "max": 150.0, "type": "float"}
    service_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.4, "max": 1.2, "type": "float"}
    extra_periods = 3.0  # OPT_PARAM: {"initial": 3.0, "min": 0.0, "max": 3.0, "type": "float"}
    damping = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    min_order = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 200.0, "type": "float"}
    max_order = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 10.0, "max": 1000.0, "type": "float"}

    L = len(pipeline_orders)
    # inventory position = on-hand + on-order (including arriving now)
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Target inventory position: expected lead-time demand scaled down to avoid excess holding + small buffer
    target_ip = mean_demand * (service_factor * L + extra_periods)

    raw_order = (target_ip - inventory_position) * damping

    # Enforce bounds
    raw_order = max(min_order, raw_order)
    raw_order = min(max_order, raw_order)

    order_amount = int(max(0, round(raw_order)))
    return order_amount
