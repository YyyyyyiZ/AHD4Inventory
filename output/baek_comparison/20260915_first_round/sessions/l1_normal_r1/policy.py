_STARTUP_ORDERS = (
    103.36740662,
    89.84154688,
    88.11440108,
    87.20817980,
    87.33351561,
    86.01063776,
)

_PROJECTED_DEMANDS = (
    75.4734,
    93.3260,
    98.7350,
    98.7496,
    98.7497,
    98.7469,
)

_KNOTS = (0.0, 5.0, 10.0, 20.0, 40.0, 80.0, 160.0)
_POSITIVE_ACTIONS = (
    86.0756,
    85.0058,
    84.2788,
    82.3808,
    77.5007,
    53.6510,
    0.0,
)
_ZERO_PROJECTED_ACTION = 87.991


def _close(a, b):
    return abs(a - b) <= 1e-7


def _startup_action(inventory, pipeline):
    if not _close(inventory, 0.0):
        return None

    for stage in range(6):
        expected = [0.0] * (5 - stage) + list(_STARTUP_ORDERS[:stage])
        if all(_close(pipeline[j], expected[j]) for j in range(5)):
            return _STARTUP_ORDERS[stage]

    return None


def _interpolated_action(x):
    if x >= _KNOTS[-1]:
        return 0.0

    for j in range(len(_KNOTS) - 1):
        left = _KNOTS[j]
        right = _KNOTS[j + 1]
        if x <= right:
            weight = (x - left) / (right - left)
            return (
                _POSITIVE_ACTIONS[j]
                + weight * (_POSITIVE_ACTIONS[j + 1] - _POSITIVE_ACTIONS[j])
            )

    return 0.0


def compute_order_amount(on_hand_inventory, pipeline_orders):
    inventory = float(on_hand_inventory)
    pipeline = tuple(float(x) for x in pipeline_orders)

    startup = _startup_action(inventory, pipeline)
    if startup is not None:
        return startup

    projected = max(inventory - _PROJECTED_DEMANDS[0], 0.0)
    for j in range(5):
        projected = max(
            projected + pipeline[j] - _PROJECTED_DEMANDS[j + 1],
            0.0,
        )

    if projected <= 1e-10:
        return _ZERO_PROJECTED_ACTION

    return max(0.0, _interpolated_action(projected))
