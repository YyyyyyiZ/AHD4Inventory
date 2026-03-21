def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 600.1  # OPT_PARAM: {"initial": 600.1, "min": 10, "max": 1000, "type": "float"}
    lead_factor = 0.15  # OPT_PARAM: {"initial": 0.15, "min": 0.0, "max": 2.0, "type": "float"}
    max_order = 500  # OPT_PARAM: {"initial": 500, "min": 0, "max": 2000, "type": "int"}
    scale_target = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.5, "max": 2.0, "type": "float"}
    pipeline_weight = 0.03  # OPT_PARAM: {"initial": 0.03, "min": 0.0, "max": 0.2, "type": "float"}
    on_hand_bias = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 2.0, "type": "float"}

    target = base_stock * lead_factor * scale_target
    sum_pipeline = sum(pipeline_orders)
    order_amount = target - on_hand_inventory * on_hand_bias - sum_pipeline * pipeline_weight
    if order_amount < 0:
        order_amount = 0
    if order_amount > max_order:
        order_amount = max_order
    return order_amount
