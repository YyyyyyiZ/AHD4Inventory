# sample_id: 068
# folder: deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r8
# distribution: poisson_L4_c1_5
# generation: 2
# rank_in_population_file: 1
# objective: 1940.21194
# test_objective: 1965.16912
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: pipeline_weighting;state_dependent_target;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 537.5676918637181  # OPT_PARAM: {"initial": 537.5676918637181, "min": 400, "max": 700, "type": "float"}
    safety_stock = 35.0  # OPT_PARAM: {"initial": 35.0, "min": 20, "max": 80, "type": "float"}
    demand_estimate = 98.5  # OPT_PARAM: {"initial": 98.5, "min": 85, "max": 115, "type": "float"}
    adjustment_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.9, "type": "float"}
    pipeline_weight = 0.5351670816616867  # OPT_PARAM: {"initial": 0.5351670816616867, "min": 0.5, "max": 1.0, "type": "float"}
    
    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight**(len(pipeline_orders)-i-1) 
                          for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)
    
    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock
    
    # Use the maximum of base_stock and target_position
    order_up_to = max(base_stock, target_position)
    
    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)
    
    # Apply adjustment factor
    order_amount = order_amount * adjustment_factor
    
    # Round to nearest integer (practical ordering)
    return order_amount
