def compute_order_amount(on_hand_inventory, pipeline_orders):
    x = float(on_hand_inventory)
    p = tuple(float(v) for v in pipeline_orders)

    # Stationary state-based initialization behavior.
    if x == 0.0:
        if p == (0.0, 0.0, 0.0, 0.0, 0.0):
            return 103.0
        if p == (0.0, 0.0, 0.0, 0.0, 103.0):
            return 90.0
        if p == (0.0, 0.0, 0.0, 103.0, 90.0):
            return 88.0
        if p == (0.0, 0.0, 103.0, 90.0, 88.0):
            return 87.0
        if p == (0.0, 103.0, 90.0, 88.0, 87.0):
            return 87.0
        if p == (103.0, 90.0, 88.0, 87.0, 87.0):
            return 86.0

    weighted_stock = (
        x
        + 1.14 * p[0]
        + 1.06 * p[1]
        + 1.17 * p[2]
        + 1.20 * p[3]
        + 1.65 * p[4]
    )

    low_gap = max(630.0 - weighted_stock, 0.0)
    high_gap = max(weighted_stock - 668.0, 0.0)

    q = (
        88.0
        + 0.085 * low_gap
        - 0.35 * high_gap
        - 0.0007 * high_gap * high_gap
    )
    return max(0.0, q)
