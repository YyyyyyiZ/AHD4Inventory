import math

_MEAN_DEMAND = 100.0
_ORDER_CAP = 82.83732902
_LINEAR_COEF = 0.82699492
_QUADRATIC_COEF = 0.24923557
_LARGE_STATE = 100000.0

def _expected_inventory_at_arrival(inventory, pipeline):
    """Expected stock just before a new order arrives, using exponential demand."""
    scale = _MEAN_DEMAND
    exp_term = math.exp(-inventory / scale)

    # moments[k] = E[X^k exp(-X/scale)]
    moments = [exp_term]
    power = 1.0
    for _ in range(6):
        power *= inventory
        moments.append(power * exp_term)

    expected = inventory

    # Current-period demand, followed by five pipeline arrivals and demands.
    for step in range(6):
        if step:
            arrival = pipeline[step - 1]
            if arrival:
                old = moments
                decay = math.exp(-arrival / scale)
                transformed = []
                max_degree = len(old) - 1

                for degree in range(max_degree + 1):
                    value = 0.0
                    for r in range(degree + 1):
                        value += (
                            math.comb(degree, r)
                            * (arrival ** (degree - r))
                            * old[r]
                        )
                    transformed.append(decay * value)

                moments = transformed
                expected += arrival

        old = moments
        expected = expected - scale + scale * old[0]
        if expected < 0.0:
            expected = 0.0

        next_moments = [old[0] + old[1] / scale]
        for degree in range(1, len(old) - 1):
            next_moments.append(old[degree + 1] / (scale * (degree + 1)))
        moments = next_moments

    return expected


def compute_order_amount(on_hand_inventory, pipeline_orders):
    inventory = float(on_hand_inventory)
    pipeline = [float(x) for x in pipeline_orders]

    # Such states already contain overwhelmingly more inventory than useful.
    if inventory >= _LARGE_STATE or any(x >= _LARGE_STATE for x in pipeline):
        return 0.0

    projected = _expected_inventory_at_arrival(inventory, pipeline)

    if projected <= 150.0:
        order = (
            _ORDER_CAP
            - _LINEAR_COEF * projected
            + (_QUADRATIC_COEF / 100.0) * projected * projected
        )
    elif projected < 200.0:
        order_at_150 = (
            _ORDER_CAP
            - 150.0 * _LINEAR_COEF
            + (_QUADRATIC_COEF / 100.0) * 150.0 * 150.0
        )
        order = order_at_150 * (200.0 - projected) / 50.0
    else:
        order = 0.0

    if order <= 0.0:
        return 0.0
    if order >= _ORDER_CAP:
        return _ORDER_CAP
    return float(order)
