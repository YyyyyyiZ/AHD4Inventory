# sample_id: 041
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_10_r5
# distribution: poisson_L6_c1_2
# generation: 3
# rank_in_population_file: 6
# objective: 1642.5
# test_objective: 1638.292
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 663.9895492381544  # OPT_PARAM: {"initial": 663.9895492381544, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 87.16738388927891  # OPT_PARAM: {"initial": 87.16738388927891, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 100.21320601001209  # OPT_PARAM: {"initial": 100.21320601001209, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.1134087362976288  # OPT_PARAM: {"initial": 0.1134087362976288, "min": 0.1, "max": 0.9, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)
    
    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock
    
    # Calculate order quantity
    order_amount = max(0, target_inventory - inventory_position)
    
    # Apply smoothing to avoid large order fluctuations
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast
    
    # Round to nearest integer (as required by output type)
    order_amount = int(round(order_amount))
    
    return order_amount
