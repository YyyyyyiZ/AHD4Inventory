def compute_order_amount(history_demand, history_inventory, history_lost, holding_cost, lost_sales_cost):
    if not history_demand:
        return 0

    # Algorithm parameters
    demand_window = 3
    momentum_factor = 0.4
    quantile_level = 0.75
    cost_sensitivity = 1.5

    # Momentum-adjusted demand forecast
    if len(history_demand) >= demand_window:
        recent_trend = history_demand[-1] - history_demand[-demand_window]
        base_forecast = sum(history_demand[-demand_window:]) / demand_window
        forecast = base_forecast + momentum_factor * recent_trend
    else:
        forecast = sum(history_demand) / len(history_demand)

    # Quantile-based safety stock
    if len(history_demand) > 1:
        sorted_demand = sorted(history_demand)
        idx = min(int(quantile_level * len(sorted_demand)), len(sorted_demand) - 1)
        safety_stock = max(0, sorted_demand[idx] - forecast)
    else:
        safety_stock = 0

    # Cost-asymmetric adjustment
    cost_ratio = (lost_sales_cost ** cost_sensitivity) / (holding_cost + lost_sales_cost ** cost_sensitivity)
    adjusted_forecast = forecast * (1 + cost_ratio)

    # Current inventory position
    inventory_position = history_inventory[-1] if history_inventory else 0

    # Order amount calculation
    order_amount = max(0, int(adjusted_forecast + safety_stock - inventory_position))

    return order_amount
