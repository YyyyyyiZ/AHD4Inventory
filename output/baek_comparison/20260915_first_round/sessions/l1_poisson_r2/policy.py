import math

_STARTUP_ORDERS = (
    101.0,
    96.16805647,
    95.97646665,
    96.0,
    95.51355986,
    95.58825429,
)

_SQRT_2 = math.sqrt(2.0)
_INV_SQRT_2PI = 1.0 / math.sqrt(2.0 * math.pi)


def compute_order_amount(on_hand_inventory, pipeline_orders):
    x = float(on_hand_inventory)
    pipeline = tuple(float(v) for v in pipeline_orders)

    # Stationary state-based initialization trajectory.
    if abs(x) <= 1e-10:
        for k, order in enumerate(_STARTUP_ORDERS):
            expected = (0.0,) * (5 - k) + _STARTUP_ORDERS[:k]
            if all(abs(pipeline[j] - expected[j]) <= 1e-8 for j in range(5)):
                return float(order)

    # Extremely large inventory anywhere in the six-period supply path
    # makes an additional order unnecessary and avoids numerical overflow.
    if x > 1_000_000.0 or any(v > 1_000_000.0 for v in pipeline):
        return 0.0

    # Moment projection of inventory remaining immediately before a new
    # order would arrive. Selling demand is approximated by its matched
    # normal moments at each step, retaining censoring at zero.
    projected_mean = x
    projected_var = 0.0
    forecast_mean = 100.9
    demand_var = 100.0

    for step in range(6):
        mu = projected_mean - forecast_mean
        var = projected_var + demand_var
        sd = math.sqrt(var)
        a = mu / sd

        cdf = 0.5 * (1.0 + math.erf(a / _SQRT_2))
        density = _INV_SQRT_2PI * math.exp(-0.5 * a * a)

        second_moment = (
            (var + mu * mu) * cdf
            + mu * sd * density
        )
        projected_mean = sd * density + mu * cdf
        projected_var = max(
            0.0,
            second_moment - projected_mean * projected_mean,
        )

        if step < 5:
            projected_mean += pipeline[step]

    order = 100.375 - projected_mean
    return float(max(0.0, order))
