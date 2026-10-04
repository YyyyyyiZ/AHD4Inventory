def compute_order_amount(on_hand_inventory, pipeline_orders):
    inv = float(on_hand_inventory)
    pipe = [float(pipeline_orders[i]) for i in range(5)]

    # Extremely large inventory positions never require an additional order.
    if inv > 1.0e12 or any(x > 1.0e12 for x in pipe):
        return 0.0

    x0 = inv / 100.0
    x1, x2, x3, x4, x5 = (x / 100.0 for x in pipe)
    total = x0 + x1 + x2 + x3 + x4 + x5

    y = (
        0.85993599
        + 0.07725468 * x0
        - 0.00544936 * x1
        - 0.02921910 * x2
        - 0.05609017 * x3
        - 0.13157163 * x4
        - 0.30589234 * x5
        + 0.04011627 * max(x0 - 0.25, 0.0)
        - 0.09958131 * max(x0 - 0.50, 0.0)
        + 0.00332507 * max(x0 - 1.00, 0.0)
        - 0.03404072 * max(x0 - 2.00, 0.0)
        + 0.01264522 * max(total - 1.0, 0.0)
        - 0.00650812 * max(total - 2.0, 0.0)
        - 0.09222451 * max(total - 3.0, 0.0)
        - 0.07757455 * max(total - 4.0, 0.0)
        - 0.12105406 * max(total - 5.0, 0.0)
        - 0.05973706 * max(total - 6.0, 0.0)
    )

    return max(0.0, 100.0 * y)
