# sample_id: 026
# folder: deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_e1-e2-m2_4_r1
# distribution: poisson_L2_c1_2
# generation: 3
# rank_in_population_file: 3
# objective: 735.84
# test_objective: 747.41
# is_top10_by_distribution: True
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;order_up_to;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Base stock level parameters
    base_stock = 258.4217014907287  # OPT_PARAM: {"initial": 258.4217014907287, "min": 150, "max": 350, "type": "float"}
    safety_stock = 22.3071877883226  # OPT_PARAM: {"initial": 22.3071877883226, "min": 5, "max": 40, "type": "float"}
    
    # Demand estimation parameters
    demand_estimation_factor = 0.7446704670998904  # OPT_PARAM: {"initial": 0.7446704670998904, "min": 0.7, "max": 1.0, "type": "float"}
    
    # Order adjustment parameters
    pipeline_adjustment_factor = 0.32566760957648905  # OPT_PARAM: {"initial": 0.32566760957648905, "min": 0.1, "max": 0.5, "type": "float"}
    order_smoothing = 0.09328880135760655  # OPT_PARAM: {"initial": 0.09328880135760655, "min": 0.0, "max": 0.3, "type": "float"}
    
    # Order constraints
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 10, "type": "int"}
    max_order = 120  # OPT_PARAM: {"initial": 120, "min": 80, "max": 200, "type": "int"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Estimate demand based on base stock level
    estimated_demand = base_stock * demand_estimation_factor / 2.0
    
    # Calculate pipeline adjustment
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_adjustment = pipeline_adjustment_factor * (estimated_demand - avg_pipeline)
    else:
        pipeline_adjustment = 0
    
    # Calculate target inventory position
    target_inventory_position = base_stock + safety_stock + pipeline_adjustment
    
    # Calculate suggested order
    suggested_order = max(0, target_inventory_position - inventory_position)
    
    # Apply smoothing
    smoothed_order = order_smoothing * suggested_order + (1 - order_smoothing) * estimated_demand
    
    # Apply constraints
    constrained_order = max(min_order, min(max_order, smoothed_order))
    
    # Round to nearest integer
    order_amount = int(round(constrained_order))
    
    return order_amount
