# sample_id: 095
# folder: deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_10_r1
# distribution: exponential_L6_c1_5
# generation: 8
# rank_in_population_file: 7
# objective: 11091.44975
# test_objective: 11183.46189
# is_top10_by_distribution: True
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 376.9532527591698  # OPT_PARAM: {"initial": 376.9532527591698, "min": 300, "max": 450, "type": "float"}
    safety_stock = 92.84179923380147  # OPT_PARAM: {"initial": 92.84179923380147, "min": 50, "max": 150, "type": "float"}
    demand_smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.6, "max": 1.0, "type": "float"}
    order_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Estimate demand from recent pipeline arrivals (last 4 periods)
    recent_arrivals = pipeline_orders[:4] if len(pipeline_orders) >= 4 else pipeline_orders
    if recent_arrivals:
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = base_stock / 8
    
    # Smooth demand estimate with stronger smoothing
    smoothed_demand = demand_smoothing * avg_recent_demand + (1 - demand_smoothing) * (base_stock / 8)
    
    # Calculate expected demand during lead time with adjusted weight
    expected_lead_time_demand = smoothed_demand * pipeline_weight * len(pipeline_orders)
    
    # Determine order-up-to level with reduced safety stock
    order_up_to = base_stock + safety_stock + expected_lead_time_demand
    
    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)
    
    # Apply stronger smoothing to order amount to reduce volatility
    if order_amount > 0:
        order_amount = order_smoothing * order_amount + (1 - order_smoothing) * smoothed_demand
    
    # Round to nearest integer (as required by output type)
    return order_amount
