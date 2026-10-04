# sample_id: 020
# folder: deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2plural_6_r6
# distribution: exponential_L6_c1_2
# generation: 1
# rank_in_population_file: 9
# objective: 7317.1
# test_objective: 7436.453
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;order_up_to
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 326.7318458492169  # OPT_PARAM: {"initial": 326.7318458492169, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 19.771688406626556  # OPT_PARAM: {"initial": 19.771688406626556, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Estimate upcoming demand based on pipeline orders (as proxy for recent orders)
    # Use average of recent pipeline orders as demand forecast
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
        forecast_demand = sum(recent_orders) / len(recent_orders) * demand_forecast_factor
    else:
        forecast_demand = 0
    
    # Adjust base stock level based on forecast
    adjusted_base_stock = base_stock + forecast_demand + safety_stock
    
    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)
    
    # Round to nearest integer (since order amounts should be integers)
    order_amount = int(round(order_amount))
    
    return order_amount
