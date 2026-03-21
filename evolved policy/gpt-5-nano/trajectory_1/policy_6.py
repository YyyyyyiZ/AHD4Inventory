def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 109.32538994689429  # OPT_PARAM: {"initial": 109.32538994689429, "min": 10.0, "max": 1000.0, "type": "float"}
    lead_factor = 1.0302849223936494  # OPT_PARAM: {"initial": 1.0302849223936494, "min": 0.0, "max": 2.0, "type": "float"}
    scale_target = 0.8700957237858957  # OPT_PARAM: {"initial": 0.8700957237858957, "min": 0.5, "max": 1.5, "type": "float"}
    max_order = 600  # OPT_PARAM: {"initial": 600, "min": 0, "max": 2000, "type": "int"}
    on_hand_bias = 0.030427965480583227  # OPT_PARAM: {"initial": 0.030427965480583227, "min": 0.0, "max": 1.0, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.0, "type": "float"}

    target = base_stock * lead_factor * scale_target
    sum_pipeline = sum(pipeline_orders)
    order_amount = target - on_hand_inventory * on_hand_bias - sum_pipeline * pipeline_weight
    if order_amount < 0:
        order_amount = 0
    if order_amount > max_order:
        order_amount = max_order
    return order_amount
