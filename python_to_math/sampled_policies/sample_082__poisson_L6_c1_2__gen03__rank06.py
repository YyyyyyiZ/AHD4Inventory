# sample_id: 082
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r8
# distribution: poisson_L6_c1_2
# generation: 3
# rank_in_population_file: 6
# objective: 1195.96
# test_objective: 1187.877
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;threshold_order_activation;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 550.0  # OPT_PARAM: {"initial": 550.0, "min": 300, "max": 800, "type": "float"}
    safety_stock = 83.79999999999248  # OPT_PARAM: {"initial": 83.79999999999248, "min": 20, "max": 150, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}
    
    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)
    
    # Calculate target inventory position with dynamic adjustment
    target_position = expected_lead_time_demand + safety_stock
    
    # Calculate order amount
    order_amount = max(0, target_position - net_inventory)
    
    # Apply smoothing factor to reduce order volatility
    smoothing_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.3, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = order_amount * smoothing_factor
    
    # Cap order amount based on recent demand pattern
    max_order = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 200, "type": "float"}
    order_amount = min(order_amount, max_order)
    
    # Minimum order quantity to avoid tiny orders
    min_order = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 30, "type": "float"}
    if 0 < order_amount < min_order:
        order_amount = min_order
    
    # Round to nearest integer since order amount must be integer
    order_amount = int(round(order_amount))
    
    return order_amount
