# sample_id: 061
# folder: deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r9
# distribution: poisson_L4_c1_5
# generation: 2
# rank_in_population_file: 5
# objective: 2035.5205
# test_objective: 2034.89705
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 437.50330001294367  # OPT_PARAM: {"initial": 437.50330001294367, "min": 400, "max": 600, "type": "float"}
    safety_stock = 47.503300012927305  # OPT_PARAM: {"initial": 47.503300012927305, "min": 20, "max": 150, "type": "float"}
    smoothing_factor = 0.31732836224038596  # OPT_PARAM: {"initial": 0.31732836224038596, "min": 0.1, "max": 0.9, "type": "float"}
    lead_time = 4  # OPT_PARAM: {"initial": 4, "min": 1, "max": 8, "type": "int"}
    demand_forecast_factor = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.5, "max": 1.2, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Estimate upcoming demand based on recent pipeline usage
    # Use average of recent orders as demand forecast
    if len(pipeline_orders) > 0:
        recent_orders_avg = sum(pipeline_orders) / len(pipeline_orders)
        forecast_adjustment = demand_forecast_factor * recent_orders_avg
    else:
        forecast_adjustment = 0
    
    # Adjust target based on forecast and lead time
    adjusted_target = base_stock + safety_stock + forecast_adjustment * lead_time
    
    # Calculate order amount with smoothing
    order_amount = max(0, smoothing_factor * (adjusted_target - inventory_position))
    
    # Round to nearest integer
    return order_amount
