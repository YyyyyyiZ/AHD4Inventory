# sample_id: 035
# folder: deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_10_r2
# distribution: poisson_L2_c1_2
# generation: 1
# rank_in_population_file: 3
# objective: 1031.2
# test_objective: 1033.424
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;order_up_to
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 294.00072750770767  # OPT_PARAM: {"initial": 294.00072750770767, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 0, "max": 100, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 150, "type": "float"}
    adjustment_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.1, "max": 1.0, "type": "float"}
    
    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time (L=2 periods)
    expected_lead_time_demand = demand_estimate * 2
    
    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock
    
    # Calculate order-up-to level
    order_up_to = max(base_stock, target_position)
    
    # Calculate order quantity with adjustment
    raw_order = max(0, order_up_to - inventory_position)
    order_amount = int(round(raw_order * adjustment_factor))
    
    return order_amount
