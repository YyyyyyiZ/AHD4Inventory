# sample_id: 098
# folder: deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7
# distribution: poisson_L6_c1_5
# generation: 6
# rank_in_population_file: 3
# objective: 3082.4
# test_objective: 3096.685
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 650.0  # OPT_PARAM: {"initial": 650.0, "min": 400, "max": 900, "type": "float"}
    safety_stock = 155.24241310755608  # OPT_PARAM: {"initial": 155.24241310755608, "min": 100, "max": 250, "type": "float"}
    demand_forecast = 105.69008621250516  # OPT_PARAM: {"initial": 105.69008621250516, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    lead_time = len(pipeline_orders)
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time plus one period
    expected_lead_time_demand = demand_forecast * (lead_time + 1)
    
    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock
    
    # Use the maximum of base_stock and target_inventory as order-up-to level
    order_up_to = max(base_stock, target_inventory)
    
    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)
    
    # Apply smoothing only when order amount is positive
    if order_amount > 0:
        order_amount = int(order_amount * smoothing_factor + 0.5)
    
    return order_amount
