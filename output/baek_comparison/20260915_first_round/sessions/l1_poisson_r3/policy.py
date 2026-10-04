import math

# Fixed policy parameters optimized for:
# lead_time=6, Poisson mean=100, holding_cost=1, lost_sales_cost=2,
# and 50 selling periods.
_TARGET = 101.93
_FORECAST_MEAN = 101.35
_VARIANCE_SCALE = 1.43
_VARIANCE_ADJUSTMENT = 0.075

_SQRT_2 = math.sqrt(2.0)
_INV_SQRT_2PI = 1.0 / math.sqrt(2.0 * math.pi)


def _positive_normal_moments(mean, variance):
    """Moments of max(X, 0) for a normal X."""
    if variance <= 0.0:
        value = max(mean, 0.0)
        return value, 0.0

    sd = math.sqrt(variance)
    z = mean / sd

    if z >= 8.0:
        return mean, variance
    if z <= -12.0:
        return 0.0, 0.0

    cdf = 0.5 * math.erfc(-z / _SQRT_2)
    density = math.exp(-0.5 * z * z) * _INV_SQRT_2PI

    positive_mean = sd * density + mean * cdf
    second_moment = (
        (mean * mean + variance) * cdf
        + mean * sd * density
    )
    positive_variance = second_moment - positive_mean * positive_mean
    if positive_variance < 0.0:
        positive_variance = 0.0

    return positive_mean, positive_variance


def compute_order_amount(on_hand_inventory, pipeline_orders):
    inventory = float(on_hand_inventory)
    pipeline = [float(x) for x in pipeline_orders]

    # Prevent unnecessary large-number arithmetic. With this much inventory
    # anywhere in the six-period supply path, the policy's order is zero.
    if inventory > 1_000_000.0 or any(x > 1_000_000.0 for x in pipeline):
        return 0.0

    projected_mean = inventory
    projected_variance = 0.0
    demand_variance = 100.0 * _VARIANCE_SCALE

    # Project inventory through the current period's demand and the following
    # five demands. Each pipeline order is added only when it arrives.
    for step in range(6):
        projected_mean, projected_variance = _positive_normal_moments(
            projected_mean - _FORECAST_MEAN,
            projected_variance + demand_variance,
        )
        if step < 5:
            projected_mean += pipeline[step]

    target = (
        _TARGET
        + _VARIANCE_ADJUSTMENT
        * (math.sqrt(projected_variance) - 10.0)
    )
    order = target - projected_mean

    if order <= 0.0:
        return 0.0
    return float(order)
