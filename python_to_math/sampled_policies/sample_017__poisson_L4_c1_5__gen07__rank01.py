# sample_id: 017
# folder: deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r6
# distribution: poisson_L4_c1_5
# generation: 7
# rank_in_population_file: 1
# objective: 2043.12
# test_objective: 2034.491
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;order_up_to;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 580.0  # OPT_PARAM: {"initial": 580.0, "min": 400, "max": 700, "type": "float"}
    safety_stock = 229.86830524581194  # OPT_PARAM: {"initial": 229.86830524581194, "min": 80, "max": 250, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    lead_time = len(pipeline_orders)
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * lead_time
    
    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock
    
    # Calculate order amount with adjustment
    order_amount = max(0, target_position - inventory_position)
    order_amount = order_amount * adjustment_factor
    
    # Apply base stock as upper bound
    max_order = max(0, base_stock - inventory_position)
    order_amount = min(order_amount, max_order)
    
    # Round to nearest integer
    order_amount = int(round(order_amount))
    
    return order_amount
