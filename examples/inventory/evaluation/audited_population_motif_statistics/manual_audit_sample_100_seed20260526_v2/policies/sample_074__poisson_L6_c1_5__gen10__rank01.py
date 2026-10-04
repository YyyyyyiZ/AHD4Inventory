# sample_id: 074
# folder: deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7
# distribution: poisson_L6_c1_5
# generation: 10
# rank_in_population_file: 1
# objective: 3074.22
# test_objective: 3077.277
# is_top10_by_distribution: False
# is_final_generation: True
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 650.0  # OPT_PARAM: {"initial": 650.0, "min": 400, "max": 900, "type": "float"}
    safety_stock = 155.24240621033815  # OPT_PARAM: {"initial": 155.24240621033815, "min": 100, "max": 250, "type": "float"}
    demand_forecast = 105.69007241806933  # OPT_PARAM: {"initial": 105.69007241806933, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.4915613763933389  # OPT_PARAM: {"initial": 0.4915613763933389, "min": 0.0, "max": 1.0, "type": "float"}
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
