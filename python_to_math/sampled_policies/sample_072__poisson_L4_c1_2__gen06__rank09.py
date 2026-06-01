# sample_id: 072
# folder: deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_10_r1
# distribution: poisson_L4_c1_2
# generation: 6
# rank_in_population_file: 9
# objective: 1009.1
# test_objective: 1014.849
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;order_up_to;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;threshold_order_activation;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 441.87238367408924  # OPT_PARAM: {"initial": 441.87238367408924, "min": 300, "max": 600, "type": "float"}
    safety_stock = 20.003514553741276  # OPT_PARAM: {"initial": 20.003514553741276, "min": 10, "max": 80, "type": "float"}
    demand_estimate = 93.33801940498932  # OPT_PARAM: {"initial": 93.33801940498932, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}
    order_threshold = 10.1  # OPT_PARAM: {"initial": 10.1, "min": 5, "max": 30, "type": "float"}
    lead_time = len(pipeline_orders)
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand over lead time plus one period
    expected_lead_time_demand = demand_estimate * (lead_time + 1)
    
    # Calculate target inventory position
    target_position = base_stock + safety_stock
    
    # Calculate order amount using base-stock policy
    order_amount = max(0, target_position - inventory_position)
    
    # Apply smoothing only when order is significant
    if order_amount > demand_estimate * 0.5:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate
    
    # Apply order threshold
    if order_amount < order_threshold:
        order_amount = 0
    
    # Round to nearest integer
    order_amount = int(round(order_amount))
    
    return order_amount
