import math
import numpy as np

_DISCOUNT = 0.95
_PURCHASE_COST = 9.025

_SQRT2 = math.sqrt(2.0)
_SQRT2PI = math.sqrt(2.0 * math.pi)
_PHI_MINUS_ONE = 0.5 * (1.0 + math.erf(-1.0 / _SQRT2))
_TRUNCATION_MASS = 1.0 - 2.0 * _PHI_MINUS_ONE


def _normal_pdf(z):
    return math.exp(-0.5 * z * z) / _SQRT2PI


def _normal_cdf(z):
    return 0.5 * (1.0 + math.erf(z / _SQRT2))


def _demand_cdf(x):
    if x <= 0.0:
        return 0.0
    if x >= 10.0:
        return 1.0
    return (
        _normal_cdf((x - 5.0) / 5.0) - _PHI_MINUS_ONE
    ) / _TRUNCATION_MASS


def _expected_below(k):
    """E[(k-D)+] for the specified truncated-normal demand."""
    clipped = min(10.0, max(0.0, k))
    z = (clipped - 5.0) / 5.0
    partial_moment = (
        5.0 * (_normal_cdf(z) - _PHI_MINUS_ONE)
        + 5.0 * (_normal_pdf(-1.0) - _normal_pdf(z))
    ) / _TRUNCATION_MASS
    return k * _demand_cdf(k) - partial_moment


def _expected_above(k):
    """E[(D-k)+] for the specified truncated-normal demand."""
    return 5.0 - k + _expected_below(k)


def _transition_and_cost(x0, x1):
    probabilities = np.zeros(21, dtype=np.float64)

    expected_cost = (
        _expected_below(x0 + x1)
        + 7.0 * _expected_below(x0)
        + 2.0 * _expected_above(x0 + x1)
        + 1000.0 * _expected_above(x0 + x1 + 10.0)
    )

    cuts = [0.0, 10.0, min(10.0, max(0.0, x0))]
    for j in range(-10, 10):
        boundary = x1 + x0 - j - 0.5
        cuts.append(min(10.0, max(0.0, boundary)))
    cuts = sorted(set(cuts))

    for low, high in zip(cuts[:-1], cuts[1:]):
        demand = 0.5 * (low + high)
        next_x0 = max(x1 - max(0.0, demand - x0), -10.0)
        rounded = int(np.rint(next_x0))
        probabilities[rounded + 10] += (
            _demand_cdf(high) - _demand_cdf(low)
        )

    return probabilities, expected_cost


def _build_policy():
    # Integrate over the unobserved position inside each rounding interval.
    nodes, weights = np.polynomial.legendre.leggauss(12)
    weights *= 0.5

    transition = np.zeros((21 * 11, 21), dtype=np.float64)
    period_cost = np.zeros(21 * 11, dtype=np.float64)

    for r_index, rounded_x0 in enumerate(range(-10, 11)):
        if rounded_x0 == -10:
            latent_values = -10.0 + 0.25 * (nodes + 1.0)
        elif rounded_x0 == 10:
            latent_values = 9.5 + 0.25 * (nodes + 1.0)
        else:
            latent_values = rounded_x0 + 0.5 * nodes

        for x1 in range(11):
            row = r_index * 11 + x1
            for weight, latent_x0 in zip(weights, latent_values):
                probabilities, cost = _transition_and_cost(
                    float(latent_x0), x1
                )
                transition[row] += weight * probabilities
                period_cost[row] += weight * cost

    value = np.zeros((21, 11, 11, 11, 11), dtype=np.float64)
    order_cost = _PURCHASE_COST * np.arange(11, dtype=np.float64)

    policy = None
    for _ in range(45):
        continuation = (
            transition @ value.reshape(21, -1)
        ).reshape(21, 11, 11, 11, 11, 11)

        action_values = (
            order_cost + _DISCOUNT * continuation
        )
        policy = np.argmin(action_values, axis=-1).astype(np.uint8)

        value = (
            period_cost.reshape(21, 11, 1, 1, 1)
            + np.min(action_values, axis=-1)
        )

    return policy


_POLICY = _build_policy()


def compute_order_amount(state):
    x0, x1, x2, x3, x4 = state
    return int(
        _POLICY[
            int(x0) + 10,
            int(x1),
            int(x2),
            int(x3),
            int(x4),
        ]
    )
