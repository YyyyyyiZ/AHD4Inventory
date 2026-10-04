# sample_id: 058
# folder: deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r8
# distribution: poisson_L6_c1_5
# generation: 7
# rank_in_population_file: 6
# objective: 2947.05251
# test_objective: 2977.16457
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 709.6025870100856  # OPT_PARAM: {"initial": 709.6025870100856, "min": 500, "max": 800, "type": "float"}
    safety_stock = 200.0  # OPT_PARAM: {"initial": 200.0, "min": 100, "max": 200, "type": "float"}
    demand_forecast = 107.5524968773776  # OPT_PARAM: {"initial": 107.5524968773776, "min": 90, "max": 110, "type": "float"}
    adjustment_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.5, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time with pipeline consideration
    lead_time = len(pipeline_orders)
    expected_lead_time_demand = demand_forecast * lead_time
    
    # Adjust target based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    pipeline_avg = pipeline_sum / max(1, lead_time)
    pipeline_adjustment = max(0, pipeline_avg - demand_forecast) * pipeline_weight * lead_time
    
    # Calculate target inventory position
    target_inventory = expected_lead_time_demand + safety_stock - pipeline_adjustment
    
    # Calculate order amount with adjustment factor
    order_needed = target_inventory - inventory_position
    order_amount = max(0, order_needed * adjustment_factor)
    
    # Apply base stock as upper bound
    order_amount = min(order_amount, max(0, base_stock - inventory_position))
    
    # Round to nearest integer since order amounts should be integers
    return order_amount
