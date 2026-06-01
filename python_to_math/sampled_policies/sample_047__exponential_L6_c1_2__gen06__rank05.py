# sample_id: 047
# folder: deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_10_r1
# distribution: exponential_L6_c1_2
# generation: 6
# rank_in_population_file: 5
# objective: 6041.04
# test_objective: 6154.832
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;order_up_to;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 367.35214483887654  # OPT_PARAM: {"initial": 367.35214483887654, "min": 300, "max": 450, "type": "float"}
    safety_stock = 45.60091931543199  # OPT_PARAM: {"initial": 45.60091931543199, "min": 40, "max": 120, "type": "float"}
    pipeline_weight = 0.9944093066156077  # OPT_PARAM: {"initial": 0.9944093066156077, "min": 0.5, "max": 1.0, "type": "float"}
    order_smoothing = 0.11124913391084858  # OPT_PARAM: {"initial": 0.11124913391084858, "min": 0.05, "max": 0.3, "type": "float"}
    demand_forecast_factor = 7.806710259511079e-14  # OPT_PARAM: {"initial": 7.806710259511079e-14, "min": 0.0, "max": 0.3, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate weighted average of recent pipeline orders as demand forecast
    if pipeline_orders:
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders))]
        weights.reverse()
        weighted_sum = sum(w * q for w, q in zip(weights, pipeline_orders))
        weight_sum = sum(weights)
        forecast_demand = weighted_sum / weight_sum if weight_sum > 0 else 0
    else:
        forecast_demand = 0
    
    # Adjust base stock level based on demand forecast
    adjusted_base = base_stock + safety_stock
    if forecast_demand > 0:
        # Adjust based on forecast deviation from average expected demand
        avg_expected_demand = base_stock / 6
        demand_adjustment = (forecast_demand - avg_expected_demand) * demand_forecast_factor
        # Limit adjustment to prevent extreme values
        demand_adjustment = max(-80, min(80, demand_adjustment))
        adjusted_base += demand_adjustment
    
    # Calculate raw order amount
    raw_order = max(0, adjusted_base - inventory_position)
    
    # Apply smoothing with forecast demand as anchor
    smoothed_order = order_smoothing * raw_order + (1 - order_smoothing) * forecast_demand
    
    # Ensure non-negative and round to integer
    order_amount = int(round(max(0, smoothed_order)))
    
    return order_amount
