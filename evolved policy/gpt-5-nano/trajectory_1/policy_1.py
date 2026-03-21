def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 600.912545747606  # OPT_PARAM: {"initial": 600.912545747606, "min": 10, "max": 1000, "type": "float"}
    lead_factor = 1.1178999673921535  # OPT_PARAM: {"initial": 1.1178999673921535, "min": 0.0, "max": 2.0, "type": "float"}
    max_order = 400  # OPT_PARAM: {"initial": 400, "min": 0, "max": 2000, "type": "int"}
    target = base_stock * lead_factor
    order_amount = target - on_hand_inventory - sum(pipeline_orders)
    if order_amount < 0:
        order_amount = 0
    if order_amount > max_order:
        order_amount = max_order
    return order_amount
