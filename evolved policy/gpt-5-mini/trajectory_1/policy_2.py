def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Estimate of average demand per period (used to size lead-time coverage)
    mean_demand = 100.16405882688387  # OPT_PARAM: {"initial": 100.16405882688387, "min": 50.0, "max": 150.0, "type": "float"}
    # Factor to scale lead-time coverage (trades off holding vs lost-sales; ~service-level)
    service_factor = 0.8674557465238618  # OPT_PARAM: {"initial": 0.8674557465238618, "min": 0.4, "max": 1.2, "type": "float"}
    # Extra coverage in units of periods (small buffer beyond scaled lead-time coverage)
    extra_periods = 2.364372319083231  # OPT_PARAM: {"initial": 2.364372319083231, "min": 0.0, "max": 3.0, "type": "float"}
    # Bounds on a single-period order
    min_order = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 200.0, "type": "float"}
    max_order = 200.0  # OPT_PARAM: {"initial": 200.0, "min": 10.0, "max": 1000.0, "type": "float"}

    L = len(pipeline_orders)
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Target inventory position: cover scaled expected demand over lead time plus small extra buffer
    target_ip = mean_demand * (service_factor * L + extra_periods)

    raw_order = target_ip - inventory_position
    raw_order = max(min_order, raw_order)
    raw_order = min(max_order, raw_order)

    order_amount = int(max(0, round(raw_order)))
    return order_amount
