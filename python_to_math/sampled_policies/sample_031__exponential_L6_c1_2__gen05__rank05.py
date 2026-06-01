# sample_id: 031
# folder: deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2plural_6_r6
# distribution: exponential_L6_c1_2
# generation: 5
# rank_in_population_file: 5
# objective: 6011.41212
# test_objective: 6126.22791
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;threshold_order_activation;emergency_or_shortage_boost
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 319.94837008016606  # OPT_PARAM: {"initial": 319.94837008016606, "min": 250, "max": 400, "type": "float"}
    safety_stock = 44.94837008016602  # OPT_PARAM: {"initial": 44.94837008016602, "min": 30, "max": 80, "type": "float"}
    smoothing_factor = 0.13367404564819818  # OPT_PARAM: {"initial": 0.13367404564819818, "min": 0.1, "max": 0.3, "type": "float"}
    demand_forecast = 99.85949394768903  # OPT_PARAM: {"initial": 99.85949394768903, "min": 80, "max": 120, "type": "float"}
    forecast_weight = 1.1015656359447512  # OPT_PARAM: {"initial": 1.1015656359447512, "min": 0.9, "max": 1.2, "type": "float"}
    pipeline_weight = 0.5380871201690676  # OPT_PARAM: {"initial": 0.5380871201690676, "min": 0.0, "max": 1.0, "type": "float"}
    recent_demand_window = 2  # OPT_PARAM: {"initial": 2, "min": 1, "max": 4, "type": "int"}
    min_order_threshold = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 10, "max": 40, "type": "float"}
    emergency_order_multiplier = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.0, "max": 2.0, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Estimate recent demand from pipeline arrivals
    if len(pipeline_orders) >= recent_demand_window:
        recent_arrivals = pipeline_orders[:recent_demand_window]
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
    
    # Apply smoothing with emergency ordering for critically low inventory
    order_amount = smoothing_factor * raw_order
    
    # Emergency ordering when inventory is very low
    if inventory_position < min_order_threshold:
        emergency_order = emergency_order_multiplier * blended_forecast
        order_amount = max(order_amount, emergency_order)
    
    # Ensure integer output
    return order_amount
