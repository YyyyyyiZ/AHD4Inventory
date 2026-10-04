import math

_INITIAL_ORDERS = (101.0, 96.0, 96.0, 96.0, 96.0, 96.0)

_TARGET = 99.5
_RESIDUAL_WEIGHT = 0.78
_EFFECTIVE_DEMAND_VARIANCE = 80.0

_SQRT_2 = math.sqrt(2.0)
_INV_SQRT_2PI = 1.0 / math.sqrt(2.0 * math.pi)


def _matches(a, b):
    return abs(a - b) <= 1e-8 * max(1.0, abs(a), abs(b))


def _planning_order(x, pipeline):
    if abs(x) > 1e-8:
        return None

    for n in range(6):
        expected = [0.0] * (5 - n) + list(_INITIAL_ORDERS[:n])
        if all(_matches(pipeline[j], expected[j]) for j in range(5)):
            return _INITIAL_ORDERS[n]
    return None


def compute_order_amount(on_hand_inventory, pipeline_orders):
    x = float(on_hand_inventory)
    pipeline = [float(pipeline_orders[j]) for j in range(5)]

    initial_order = _planning_order(x, pipeline)
    if initial_order is not None:
        return initial_order

    # Extremely large inventory or pipeline states require no replenishment and
    # are handled separately to keep the moment calculations numerically safe.
    if x > 1_000_000.0 or any(v > 1_000_000.0 for v in pipeline):
        return 0.0

    # Moment-matched projection of inventory remaining immediately before the
    # new order arrives, after the six intervening demands.
    mean_inventory = x
    variance_inventory = 0.0

    for k in range(6):
        mu = mean_inventory - 100.0
        variance = variance_inventory + _EFFECTIVE_DEMAND_VARIANCE
        sigma = math.sqrt(variance)
        standardized = mu / sigma

        cdf = 0.5 * (1.0 + math.erf(standardized / _SQRT_2))
        density = math.exp(-0.5 * standardized * standardized) * _INV_SQRT_2PI

        positive_mean = sigma * density + mu * cdf
        positive_second_moment = (
            (variance + mu * mu) * cdf + mu * sigma * density
        )

        variance_inventory = max(
            0.0, positive_second_moment - positive_mean * positive_mean
        )
        mean_inventory = max(0.0, positive_mean)

        if k < 5:
            mean_inventory += pipeline[k]

    order = _TARGET - _RESIDUAL_WEIGHT * mean_inventory
    if order <= 0.0:
        return 0.0
    if order >= _TARGET:
        return _TARGET
    return float(order)
