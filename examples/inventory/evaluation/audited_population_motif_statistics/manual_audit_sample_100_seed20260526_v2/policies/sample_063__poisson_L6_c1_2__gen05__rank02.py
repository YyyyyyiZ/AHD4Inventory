# sample_id: 063
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r8
# distribution: poisson_L6_c1_2
# generation: 5
# rank_in_population_file: 2
# objective: 761.06286
# test_objective: 746.02634
# is_top10_by_distribution: True
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 663.9895492381544  # OPT_PARAM: {"initial": 663.9895492381544, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 58.68920289468093  # OPT_PARAM: {"initial": 58.68920289468093, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 125.95458012582644  # OPT_PARAM: {"initial": 125.95458012582644, "min": 50, "max": 150, "type": "float"}
    
    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)
    
    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock
    
    # Calculate order amount
    order_amount = max(0, target_position - net_inventory)
    
    # Cap order amount to avoid excessive ordering
    max_order = 95.92075836350209  # OPT_PARAM: {"initial": 95.92075836350209, "min": 50, "max": 500, "type": "float"}
    order_amount = min(order_amount, max_order)
    
    return order_amount
