# sample_id: 003
# folder: deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_10_r3
# distribution: poisson_L6_c1_5
# generation: 2
# rank_in_population_file: 6
# objective: 3336.88008
# test_objective: 3369.77227
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 697.9997255235969  # OPT_PARAM: {"initial": 697.9997255235969, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 79.3000000000116  # OPT_PARAM: {"initial": 79.3000000000116, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 149.9  # OPT_PARAM: {"initial": 149.9, "min": 50, "max": 150, "type": "float"}
    lead_time = len(pipeline_orders)
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * lead_time
    
    # Calculate target inventory position
    target_inventory = expected_lead_time_demand + safety_stock
    
    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)
    
    # Apply base stock as upper bound
    order_amount = min(order_amount, max(0, base_stock - inventory_position))
    
    return order_amount
