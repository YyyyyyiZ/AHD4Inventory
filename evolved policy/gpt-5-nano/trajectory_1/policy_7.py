def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 105.22204667267495  # OPT_PARAM: {"initial": 105.22204667267495, "min": 10.0, "max": 1000.0, "type": "float"}
    lead_factor = 1.0054001648423674  # OPT_PARAM: {"initial": 1.0054001648423674, "min": 0.0, "max": 2.0, "type": "float"}
    scale_target = 0.8115940279806373  # OPT_PARAM: {"initial": 0.8115940279806373, "min": 0.5, "max": 1.5, "type": "float"}
    max_order = 600  # OPT_PARAM: {"initial": 600, "min": 0, "max": 2000, "type": "int"}
    on_hand_bias = 0.03310836331138493  # OPT_PARAM: {"initial": 0.03310836331138493, "min": 0.0, "max": 1.0, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.0, "type": "float"}
    risk_adjust = 0.1470141396356545  # OPT_PARAM: {"initial": 0.1470141396356545, "min": -0.5, "max": 0.5, "type": "float"}

    target = base_stock * lead_factor * scale_target
    sum_pipeline = sum(pipeline_orders)
    raw_order = target - on_hand_inventory * on_hand_bias - sum_pipeline * pipeline_weight
    adjusted_order = raw_order * (1 + risk_adjust)
    order_amount = int(round(adjusted_order))
    if order_amount < 0:
        order_amount = 0
    if order_amount > max_order:
        order_amount = max_order
    return order_amount
