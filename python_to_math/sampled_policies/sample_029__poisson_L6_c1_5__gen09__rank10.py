# sample_id: 029
# folder: deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_10_r1
# distribution: poisson_L6_c1_5
# generation: 9
# rank_in_population_file: 10
# objective: 1326.06
# test_objective: 1381.561
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;threshold_order_activation;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 641.7661796828763  # OPT_PARAM: {"initial": 641.7661796828763, "min": 500, "max": 700, "type": "float"}
    safety_stock = 70.0  # OPT_PARAM: {"initial": 70.0, "min": 50, "max": 150, "type": "float"}
    demand_estimate = 97.29811863847306  # OPT_PARAM: {"initial": 97.29811863847306, "min": 95, "max": 105, "type": "float"}
    lead_time_multiplier = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.0, "max": 1.3, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.1, "type": "float"}
    order_threshold = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 10, "max": 50, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_estimate * lead_time * lead_time_multiplier
    
    # Calculate target inventory level
    target_inventory = lead_time_demand + safety_stock
    
    # Use the minimum of base_stock and target_inventory
    order_up_to = min(base_stock, target_inventory)
    
    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)
    
    # Apply smoothing only when order amount is above threshold
    if order_amount > order_threshold:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate
    
    # Round to nearest integer
    order_amount = int(round(order_amount))
    
    return order_amount
