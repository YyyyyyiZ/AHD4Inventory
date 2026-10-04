# sample_id: 033
# folder: deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r6
# distribution: poisson_L6_c1_5
# generation: 6
# rank_in_population_file: 7
# objective: 1169.10026
# test_objective: 1237.16751
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;order_up_to;state_dependent_target;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 711.3122885869875  # OPT_PARAM: {"initial": 711.3122885869875, "min": 400, "max": 800, "type": "float"}
    safety_stock = 80.97700274721207  # OPT_PARAM: {"initial": 80.97700274721207, "min": 30, "max": 150, "type": "float"}
    demand_forecast = 105.6294716556608  # OPT_PARAM: {"initial": 105.6294716556608, "min": 80, "max": 120, "type": "float"}
    max_order = 98.96898380462649  # OPT_PARAM: {"initial": 98.96898380462649, "min": 80, "max": 200, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time plus review period
    expected_demand = demand_forecast * (len(pipeline_orders) + 1)
    
    # Calculate target inventory position
    target_position = expected_demand + safety_stock
    
    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)
    
    # Apply maximum order constraint
    order_amount = min(order_amount, max_order)
    
    # Apply base stock as upper bound
    if inventory_position + order_amount > base_stock:
        order_amount = max(0, base_stock - inventory_position)
    
    return order_amount
