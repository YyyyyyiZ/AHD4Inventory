def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    S_over_mean = 0.6500219464897067  # OPT_PARAM: {"initial": 0.6500219464897067, "min": 0.0, "max": 3.0, "type": "float"}
    cap_over_mean = 3.7084022533834244  # OPT_PARAM: {"initial": 3.7084022533834244, "min": 0.0, "max": 6.0, "type": "float"}
    target_forecast_gain = 0.6110176596104178  # OPT_PARAM: {"initial": 0.6110176596104178, "min": -1.0, "max": 3.0, "type": "float"}
    cap_forecast_gain = 6.99857811499404  # OPT_PARAM: {"initial": 6.99857811499404, "min": -1.0, "max": 7.0, "type": "float"}
    inventory_gain = 1.5178196587609198  # OPT_PARAM: {"initial": 1.5178196587609198, "min": 0.0, "max": 2.0, "type": "float"}
    mean_demand = 100.0
    arrival_mean = conditional_arrival_mean(last_demand, quoted_lead_time)
    projected_inventory = conditional_projected_inventory(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time)
    target = max(0.0, mean_demand * S_over_mean + target_forecast_gain * (arrival_mean - mean_demand))
    cap = max(0.0, mean_demand * cap_over_mean + cap_forecast_gain * (arrival_mean - mean_demand))
    order_amount = min(cap, max(0.0, target - inventory_gain * projected_inventory))
    return order_amount
