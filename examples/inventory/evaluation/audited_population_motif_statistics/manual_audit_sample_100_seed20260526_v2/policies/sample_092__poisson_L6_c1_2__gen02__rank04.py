# sample_id: 092
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r8
# distribution: poisson_L6_c1_2
# generation: 2
# rank_in_population_file: 4
# objective: 837.76535
# test_objective: 831.8376
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;order_up_to;partial_adjustment;order_clipping
# extra_motifs: pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 600.0  # OPT_PARAM: {"initial": 600.0, "min": 300, "max": 600, "type": "float"}
    demand_estimate = 116.45698343699016  # OPT_PARAM: {"initial": 116.45698343699016, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.2476408897165149  # OPT_PARAM: {"initial": 0.2476408897165149, "min": 0.1, "max": 0.9, "type": "float"}
    min_order = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 50, "type": "float"}
    max_order = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 200, "type": "float"}
    
    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)
    
    # Calculate target inventory position with smoothing
    target_position = base_stock
    
    # Calculate order amount with smoothing
    order_amount = max(0, target_position - net_inventory)
    
    # Apply smoothing to reduce order volatility
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate
    
    # Apply order limits
    order_amount = max(min_order, min(order_amount, max_order))
    
    return order_amount
