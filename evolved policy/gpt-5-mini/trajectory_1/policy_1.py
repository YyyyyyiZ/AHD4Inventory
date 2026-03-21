def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 600.0  # OPT_PARAM: {"initial": 600.0, "min": 10, "max": 1000, "type": "float"}
    min_order = 0.0     # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 500.0, "type": "float"}
    max_order = 200.0   # OPT_PARAM: {"initial": 200.0, "min": 0.0, "max": 2000.0, "type": "float"}

    inventory_position = on_hand_inventory + sum(pipeline_orders)
    raw_order = base_stock - inventory_position
    raw_order = max(min_order, raw_order)
    raw_order = min(max_order, raw_order)
    order_amount = int(max(0, round(raw_order)))
    return order_amount
