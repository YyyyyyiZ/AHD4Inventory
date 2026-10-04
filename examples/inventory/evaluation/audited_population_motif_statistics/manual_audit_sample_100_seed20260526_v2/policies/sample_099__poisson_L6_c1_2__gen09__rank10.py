# sample_id: 099
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_10_r4
# distribution: poisson_L6_c1_2
# generation: 9
# rank_in_population_file: 10
# objective: 1045.24
# test_objective: 1018.631
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: pipeline_demand_proxy;threshold_order_activation;integer_rounding;emergency_or_shortage_boost
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 664.104497870118  # OPT_PARAM: {"initial": 664.104497870118, "min": 650, "max": 850, "type": "float"}
    demand_estimate = 91.62096643311519  # OPT_PARAM: {"initial": 91.62096643311519, "min": 90, "max": 110, "type": "float"}
    safety_factor = 1.0669489657821407  # OPT_PARAM: {"initial": 1.0669489657821407, "min": 1.05, "max": 1.25, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    critical_ratio = 0.65  # OPT_PARAM: {"initial": 0.65, "min": 0.65, "max": 0.75, "type": "float"}
    min_order_threshold = 0.28315518642390647  # OPT_PARAM: {"initial": 0.28315518642390647, "min": 0.05, "max": 0.3, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time with safety factor
    expected_lead_time_demand = demand_estimate * len(pipeline_orders) * safety_factor
    
    # Adjust base stock based on critical ratio (p/(p+h) = 2/3)
    # Higher critical ratio means we should carry more inventory
    adjusted_base_stock = base_stock * (1 + (critical_ratio - 0.6667) * 0.5)
    
    # Calculate order-up-to level
    order_up_to = max(adjusted_base_stock, expected_lead_time_demand)
    
    # Calculate base order amount
    base_order = max(0, order_up_to - inventory_position)
    
    # Apply smoothing only when order is significant
    if base_order > demand_estimate * min_order_threshold:
        # Blend between demand-based ordering and gap-filling
        demand_based = demand_estimate * (1 + safety_factor * 0.1)
        order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_based
    else:
        order_amount = base_order
    
    # Incorporate pipeline information to smooth ordering
    if order_amount > 0:
        # Weight between current order and demand forecast
        order_amount = order_amount * pipeline_weight + demand_estimate * (1 - pipeline_weight)
    
    # Round to nearest integer
    order_amount = int(round(order_amount))
    
    return order_amount
