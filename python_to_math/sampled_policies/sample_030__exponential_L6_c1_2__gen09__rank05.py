# sample_id: 030
# folder: deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2plural_6_r6
# distribution: exponential_L6_c1_2
# generation: 9
# rank_in_population_file: 5
# objective: 6003.88807
# test_objective: 6125.17677
# is_top10_by_distribution: True
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;threshold_order_activation;emergency_or_shortage_boost
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 349.93516183417404  # OPT_PARAM: {"initial": 349.93516183417404, "min": 250, "max": 450, "type": "float"}
    safety_stock = 44.935161834169534  # OPT_PARAM: {"initial": 44.935161834169534, "min": 30, "max": 80, "type": "float"}
    smoothing_factor = 0.10743259195308223  # OPT_PARAM: {"initial": 0.10743259195308223, "min": 0.05, "max": 0.3, "type": "float"}
    demand_forecast = 99.83223131359875  # OPT_PARAM: {"initial": 99.83223131359875, "min": 80, "max": 120, "type": "float"}
    forecast_weight = 1.2051163998324366  # OPT_PARAM: {"initial": 1.2051163998324366, "min": 0.9, "max": 1.3, "type": "float"}
    pipeline_weight = 0.4512560796313605  # OPT_PARAM: {"initial": 0.4512560796313605, "min": 0.0, "max": 1.0, "type": "float"}
    min_order = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 10, "max": 40, "type": "float"}
    emergency_multiplier = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.0, "max": 2.0, "type": "float"}
    recent_window = 2  # OPT_PARAM: {"initial": 2, "min": 1, "max": 4, "type": "int"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Estimate recent demand from pipeline arrivals
    if len(pipeline_orders) >= recent_window:
        recent_arrivals = pipeline_orders[:recent_window]
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = demand_forecast
    
    # Blend static forecast with recent demand signal
    blended_forecast = (1 - pipeline_weight) * demand_forecast + pipeline_weight * avg_recent_demand
    
    # Calculate expected lead time demand
    lead_time = len(pipeline_orders)
    expected_lead_time_demand = blended_forecast * lead_time
    
    # Dynamic target: base stock + forecast-adjusted component
    dynamic_target = base_stock + forecast_weight * expected_lead_time_demand
    
    # Final target with safety stock
    target_inventory = dynamic_target + safety_stock
    
    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)
    
    # Apply smoothing
    order_amount = smoothing_factor * raw_order
    
    # Emergency ordering for critically low inventory
    if inventory_position < min_order:
        emergency_order = emergency_multiplier * blended_forecast
        order_amount = max(order_amount, emergency_order)
    
    # Ensure minimum order when raw order is significant
    if raw_order > 0 and order_amount < min_order:
        order_amount = max(order_amount, min_order)
    
    # Round to nearest integer
    return order_amount
