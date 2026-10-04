# sample_id: 089
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_10_r2
# distribution: poisson_L6_c1_2
# generation: 4
# rank_in_population_file: 5
# objective: 2229.92
# test_objective: 2232.607
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 520.0  # OPT_PARAM: {"initial": 520.0, "min": 300, "max": 800, "type": "float"}
    safety_stock = 60.0  # OPT_PARAM: {"initial": 60.0, "min": 20, "max": 150, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 80, "max": 120, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time plus one period
    expected_lead_time_demand = demand_estimate * (len(pipeline_orders) + 1)
    
    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock
    
    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)
    
    # Apply smoothing to avoid large order fluctuations
    smoothing_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount
    
    # Cap order amount based on demand forecast
    max_order = demand_estimate * 2.5  # OPT_PARAM: {"initial": 2.5, "min": 2.0, "max": 5.0, "type": "float"}
    order_amount = min(order_amount, max_order)
    
    # Ensure minimum order quantity for efficiency
    min_order = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 50, "type": "float"}
    if order_amount > 0 and order_amount < min_order:
        order_amount = min_order
    
    # Round to nearest integer
    order_amount = int(round(order_amount))
    
    return order_amount
