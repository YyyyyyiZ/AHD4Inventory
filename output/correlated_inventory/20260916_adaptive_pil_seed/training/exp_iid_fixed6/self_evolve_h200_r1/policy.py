def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    S_over_mean = 0.6947359785890602  # OPT_PARAM: {"initial": 0.6947359785890602, "min": 0.0, "max": 3.0, "type": "float"}
    cap_over_mean = 0.6026125679822039  # OPT_PARAM: {"initial": 0.6026125679822039, "min": 0.0, "max": 6.0, "type": "float"}
    target_forecast_gain = 0.0  # OPT_PARAM: {"initial": 0.0, "min": -1.0, "max": 3.0, "type": "float"}
    cap_forecast_gain = 0.1  # OPT_PARAM: {"initial": 0.1, "min": -1.0, "max": 3.0, "type": "float"}
    inventory_gain = 0.2894902604285071  # OPT_PARAM: {"initial": 0.2894902604285071, "min": 0.0, "max": 2.0, "type": "float"}
    mean_demand = 100.0
    arrival_mean = conditional_arrival_mean(last_demand, quoted_lead_time)
    projected_inventory = conditional_projected_inventory(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time)
    target = max(0.0, mean_demand * S_over_mean + target_forecast_gain * (arrival_mean - mean_demand))
    cap = max(0.0, mean_demand * cap_over_mean + cap_forecast_gain * (arrival_mean - mean_demand))
    order_amount = min(cap, max(0.0, target - inventory_gain * projected_inventory))
    return order_amount
