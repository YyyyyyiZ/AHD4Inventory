# sample_id: 052
# folder: deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r7
# distribution: poisson_L6_c1_5
# generation: 3
# rank_in_population_file: 2
# objective: 2474.85996
# test_objective: 2323.33752
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 647.9228012866358  # OPT_PARAM: {"initial": 647.9228012866358, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 98.02280128663519  # OPT_PARAM: {"initial": 98.02280128663519, "min": 0, "max": 300, "type": "float"}
    smoothing_factor = 0.4406616715947892  # OPT_PARAM: {"initial": 0.4406616715947892, "min": 0.1, "max": 1.0, "type": "float"}
    demand_forecast_factor = 0.7696949899212768  # OPT_PARAM: {"initial": 0.7696949899212768, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_weight = 0.4176510997345094  # OPT_PARAM: {"initial": 0.4176510997345094, "min": 0.0, "max": 0.8, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand based on recent pipeline arrivals
    # Use average of recent pipeline arrivals as demand proxy
    recent_arrivals = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
    expected_demand = sum(recent_arrivals) / max(len(recent_arrivals), 1) * demand_forecast_factor
    
    # Adjust target based on expected demand and pipeline composition
    pipeline_variability = max(pipeline_orders) - min(pipeline_orders) if pipeline_orders else 0
    pipeline_adjustment = pipeline_variability * pipeline_weight
    
    # Dynamic target that responds to demand patterns
    dynamic_target = base_stock + safety_stock + expected_demand - pipeline_adjustment
    
    # Calculate order with smoothing
    raw_order = dynamic_target - inventory_position
    order_amount = max(0, smoothing_factor * raw_order)
    
    # Round to nearest integer
    return order_amount
