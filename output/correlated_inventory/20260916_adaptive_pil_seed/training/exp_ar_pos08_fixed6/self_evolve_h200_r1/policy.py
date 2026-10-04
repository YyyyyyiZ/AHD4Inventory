def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    S_over_mean = 0.5186486451580228  # OPT_PARAM: {"initial": 0.5186486451580228, "min": 0.0, "max": 3.0, "type": "float"}
    cap_over_mean = 5.999770074431636  # OPT_PARAM: {"initial": 5.999770074431636, "min": 0.0, "max": 12.0, "type": "float"}
    target_forecast_gain = 0.555355051424036  # OPT_PARAM: {"initial": 0.555355051424036, "min": -1.0, "max": 3.0, "type": "float"}
    cap_forecast_gain = 6.999673149207933  # OPT_PARAM: {"initial": 6.999673149207933, "min": -1.0, "max": 15.0, "type": "float"}
    inventory_gain = 0.856843614619225  # OPT_PARAM: {"initial": 0.856843614619225, "min": 0.0, "max": 2.0, "type": "float"}
    mean_demand = 100.0
    arrival_mean = conditional_arrival_mean(last_demand, quoted_lead_time)
    projected_inventory = conditional_projected_inventory(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time)
    target = max(0.0, mean_demand * S_over_mean + target_forecast_gain * (arrival_mean - mean_demand))
    cap = max(0.0, mean_demand * cap_over_mean + cap_forecast_gain * (arrival_mean - mean_demand))
    order_amount = min(cap, max(0.0, target - inventory_gain * projected_inventory))
    return order_amount
