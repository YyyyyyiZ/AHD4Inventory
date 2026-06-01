# sample_id: 049
# folder: deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_10_r2
# distribution: poisson_L4_c1_2
# generation: 1
# rank_in_population_file: 9
# objective: 1829.22
# test_objective: 1842.556
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;order_up_to;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 415.75040145040623  # OPT_PARAM: {"initial": 415.75040145040623, "min": 300, "max": 600, "type": "float"}
    safety_stock = 45.75040145039649  # OPT_PARAM: {"initial": 45.75040145039649, "min": 20, "max": 150, "type": "float"}
    demand_forecast_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Estimate upcoming demand based on recent pipeline arrivals
    # Use average of recent pipeline orders as demand forecast
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-min(3, len(pipeline_orders)):]  # Last 3 orders
        forecast_demand = sum(recent_orders) / len(recent_orders) * demand_forecast_factor
    else:
        forecast_demand = 100.0  # Default forecast
    
    # Adjust base stock level based on forecast
    adjusted_base_stock = base_stock + safety_stock + forecast_demand * 0.5
    
    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)
    
    # Round to nearest integer (since order amounts should be integers)
    order_amount = int(round(order_amount))
    
    return order_amount
