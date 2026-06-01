# sample_id: 010
# folder: deepseek-chat_normal_std10_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r8
# distribution: normal_std10_L6_c1_2
# generation: 7
# rank_in_population_file: 6
# objective: 725.9
# test_objective: 771.368
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;order_up_to;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 503.37232950779367  # OPT_PARAM: {"initial": 503.37232950779367, "min": 400, "max": 700, "type": "float"}
    safety_stock = 86.71422918452267  # OPT_PARAM: {"initial": 86.71422918452267, "min": 50, "max": 150, "type": "float"}
    demand_estimate = 95.30195205059414  # OPT_PARAM: {"initial": 95.30195205059414, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.3, "type": "float"}
    order_cap_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 3.0, "type": "float"}
    pipeline_weight = 0.13743730510232083  # OPT_PARAM: {"initial": 0.13743730510232083, "min": 0.1, "max": 1.0, "type": "float"}
    lost_sales_weight = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 0.5, "max": 2.0, "type": "float"}
    demand_adjustment = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.5, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    expected_lead_time_demand = demand_estimate * lead_time * demand_adjustment
    
    # Simplified safety stock adjustment
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / lead_time
        pipeline_variability = abs(avg_pipeline - demand_estimate) / (demand_estimate + 1e-6)
        adjusted_safety = safety_stock * (1 + pipeline_weight * pipeline_variability)
    else:
        adjusted_safety = safety_stock
    
    # Cost-adjusted safety stock
    cost_adjusted_safety = adjusted_safety * lost_sales_weight
    
    # Calculate target inventory position
    target_position = base_stock + cost_adjusted_safety
    
    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)
    
    # Dynamic order cap
    smoothed_demand = demand_estimate + smoothing_factor * cost_adjusted_safety
    max_order = order_cap_multiplier * smoothed_demand
    order_amount = min(order_amount, max_order)
    
    # Ensure integer order amount
    order_amount = int(round(order_amount))
    
    return order_amount
