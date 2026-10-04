# sample_id: 060
# folder: deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2plural_2_r6
# distribution: exponential_L6_c1_5
# generation: 4
# rank_in_population_file: 4
# objective: 11112.78
# test_objective: 11227.361
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 517.9333077084599  # OPT_PARAM: {"initial": 517.9333077084599, "min": 400, "max": 700, "type": "float"}
    safety_stock = 118.14102434624172  # OPT_PARAM: {"initial": 118.14102434624172, "min": 80, "max": 200, "type": "float"}
    lead_time = len(pipeline_orders)
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time using recent arrivals
    # Use first 3 pipeline orders (recently arrived) as proxy for demand
    if len(pipeline_orders) >= 3:
        recent_demand = pipeline_orders[0] + pipeline_orders[1] + pipeline_orders[2]
        avg_recent_demand = recent_demand / 3.0
    else:
        avg_recent_demand = sum(pipeline_orders) / max(len(pipeline_orders), 1)
    
    # Dynamic adjustment based on recent demand
    demand_adjustment_factor = 0.8334838024453708  # OPT_PARAM: {"initial": 0.8334838024453708, "min": 0.5, "max": 1.2, "type": "float"}
    demand_adjustment = avg_recent_demand * lead_time * demand_adjustment_factor
    
    # Calculate target inventory position
    target_position = base_stock + safety_stock + demand_adjustment
    
    # Calculate raw order needed
    raw_order = max(0, target_position - inventory_position)
    
    # Apply moderate smoothing to balance responsiveness and stability
    smoothing_factor = 0.16708542784709138  # OPT_PARAM: {"initial": 0.16708542784709138, "min": 0.15, "max": 0.4, "type": "float"}
    smoothed_order = smoothing_factor * raw_order
    
    # Add small adjustment based on pipeline variability
    if len(pipeline_orders) >= 2:
        pipeline_variance = max(pipeline_orders) - min(pipeline_orders)
        variance_factor = 0.023639962573094874  # OPT_PARAM: {"initial": 0.023639962573094874, "min": 0.01, "max": 0.15, "type": "float"}
        variance_adjustment = pipeline_variance * variance_factor
        smoothed_order += variance_adjustment
    
    # Round to nearest integer
    order_amount = int(round(smoothed_order))
    
    return order_amount
