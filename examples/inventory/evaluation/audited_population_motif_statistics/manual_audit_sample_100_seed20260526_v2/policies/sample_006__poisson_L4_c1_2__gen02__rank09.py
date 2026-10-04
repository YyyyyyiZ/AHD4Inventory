# sample_id: 006
# folder: deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_10_r2
# distribution: poisson_L4_c1_2
# generation: 2
# rank_in_population_file: 9
# objective: 1727.94079
# test_objective: 1745.73919
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;order_up_to
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 430.7383762019312  # OPT_PARAM: {"initial": 430.7383762019312, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 0.033629772620031445  # OPT_PARAM: {"initial": 0.033629772620031445, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 51.26511638307087  # OPT_PARAM: {"initial": 51.26511638307087, "min": 50, "max": 150, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.0, "max": 1.0, "type": "float"}
    
    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline
    
    # Adjust base stock based on recent demand pattern
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    if recent_arrivals > 0:
        demand_adjustment = min(demand_forecast, recent_arrivals * 1.2)
    else:
        demand_adjustment = demand_forecast
    
    # Dynamic target inventory level
    target_inventory = base_stock + safety_stock + demand_adjustment
    
    # Calculate order amount with smoothing
    order_amount = max(0, target_inventory - inventory_position)
    
    # Round to nearest integer (as required by output type)
    return order_amount
