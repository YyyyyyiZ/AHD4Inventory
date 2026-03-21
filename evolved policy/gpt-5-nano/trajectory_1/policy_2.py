def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 604.8474590726188  # OPT_PARAM: {"initial": 604.8474590726188, "min": 10, "max": 1000, "type": "float"}
    lead_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.0, "max": 2.0, "type": "float"}
    max_order = 400  # OPT_PARAM: {"initial": 400, "min": 0, "max": 2000, "type": "int"}
    scale_target = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 0.5, "max": 1.5, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 2.0, "type": "float"}
    on_hand_bias = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 2.0, "type": "float"}

    target = base_stock * lead_factor * scale_target
    sum_pipeline = sum(pipeline_orders)
    order_amount = target - on_hand_inventory * on_hand_bias - sum_pipeline * pipeline_weight
    if order_amount < 0:
        order_amount = 0
    if order_amount > max_order:
        order_amount = max_order
    return order_amount
