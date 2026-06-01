# sample_id: 002
# folder: deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r6
# distribution: poisson_L4_c1_5
# generation: 6
# rank_in_population_file: 4
# objective: 2121.78
# test_objective: 2139.074
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;order_up_to;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 620.0  # OPT_PARAM: {"initial": 620.0, "min": 500, "max": 750, "type": "float"}
    safety_stock = 193.25820241595864  # OPT_PARAM: {"initial": 193.25820241595864, "min": 100, "max": 200, "type": "float"}
    demand_estimate = 110.0  # OPT_PARAM: {"initial": 110.0, "min": 90, "max": 110, "type": "float"}
    adjustment_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.0, "type": "float"}
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
