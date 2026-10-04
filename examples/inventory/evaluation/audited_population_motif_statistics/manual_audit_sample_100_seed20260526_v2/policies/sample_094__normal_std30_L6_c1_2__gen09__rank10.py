# sample_id: 094
# folder: deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2plural_6_r6
# distribution: normal_std30_L6_c1_2
# generation: 9
# rank_in_population_file: 10
# objective: 4095.46
# test_objective: 4122.034
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: pipeline_weighting;order_up_to;state_dependent_target;partial_adjustment;order_smoothing
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 530.0  # OPT_PARAM: {"initial": 530.0, "min": 400, "max": 700, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 20, "max": 100, "type": "float"}
    demand_estimate = 118.0  # OPT_PARAM: {"initial": 118.0, "min": 90, "max": 130, "type": "float"}
    pipeline_weight = 0.97  # OPT_PARAM: {"initial": 0.97, "min": 0.8, "max": 1.0, "type": "float"}
    smoothing_factor = 0.95  # OPT_PARAM: {"initial": 0.95, "min": 0.5, "max": 1.0, "type": "float"}
    cost_ratio_adjust = 0.667  # OPT_PARAM: {"initial": 0.667, "min": 0.5, "max": 0.8, "type": "float"}
    pipeline_discount = 0.95  # OPT_PARAM: {"initial": 0.95, "min": 0.8, "max": 1.0, "type": "float"}
    
    # Calculate weighted pipeline inventory with stronger discount for older orders
    weighted_pipeline = sum(p * (pipeline_weight ** i) * (pipeline_discount ** i) 
                           for i, p in enumerate(reversed(pipeline_orders)))
    
    # Calculate net inventory position with weighted pipeline
    net_inventory = on_hand_inventory + weighted_pipeline
    
    # Adjust safety stock based on cost ratio (p=2, h=1) -> optimal critical ratio = p/(p+h) = 2/3
    adjusted_safety_stock = safety_stock * cost_ratio_adjust
    
    # Calculate expected demand coverage for lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)
    
    # Calculate target inventory position
    target_position = lead_time_demand + adjusted_safety_stock
    
    # Calculate raw order amount
    raw_order = max(0, target_position - net_inventory)
    
    # Apply base stock as upper bound
    base_stock_order = max(0, base_stock - net_inventory)
    order_amount = min(raw_order, base_stock_order)
    
    # Smooth ordering using previous order if available
    if len(pipeline_orders) > 0:
        previous_order = pipeline_orders[-1]
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * previous_order
    
    # Ensure non-negative integer order
    order_amount = max(0, int(round(order_amount)))
    
    return order_amount
