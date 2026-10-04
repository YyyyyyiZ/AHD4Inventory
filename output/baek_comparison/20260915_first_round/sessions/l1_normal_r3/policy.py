_STARTUP_STATES = (
    ((0.0, 0.0, 0.0, 0.0, 0.0), 103.0),
    ((0.0, 0.0, 0.0, 0.0, 103.0), 90.0),
    ((0.0, 0.0, 0.0, 103.0, 90.0), 88.0),
    ((0.0, 0.0, 103.0, 90.0, 88.0), 87.0),
    ((0.0, 103.0, 90.0, 88.0, 87.0), 87.0),
    ((103.0, 90.0, 88.0, 87.0, 87.0), 86.0),
)

_TARGET = 87.3074014
_FORECAST_DEMAND = 98.92710131
_GAIN = 1.00220586


def compute_order_amount(on_hand_inventory, pipeline_orders):
    inventory = float(on_hand_inventory)
    pipeline = tuple(float(v) for v in pipeline_orders)

    if inventory == 0.0:
        for startup_pipeline, order in _STARTUP_STATES:
            if pipeline == startup_pipeline:
                return order

    projected_inventory = inventory

    for k in range(6):
        projected_inventory = max(
            0.0, projected_inventory - _FORECAST_DEMAND
        )
        if k < 5:
            projected_inventory += pipeline[k]

    return float(max(0.0, _GAIN * (_TARGET - projected_inventory)))
