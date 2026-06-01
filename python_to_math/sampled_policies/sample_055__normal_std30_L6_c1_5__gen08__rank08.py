# sample_id: 055
# folder: deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r8
# distribution: normal_std30_L6_c1_5
# generation: 8
# rank_in_population_file: 8
# objective: 3872.97736
# test_objective: 3848.71283
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 979.5288931101101  # OPT_PARAM: {"initial": 979.5288931101101, "min": 800, "max": 1100, "type": "float"}
    safety_stock = 201.36307898735558  # OPT_PARAM: {"initial": 201.36307898735558, "min": 100, "max": 250, "type": "float"}
    demand_estimate = 92.62607902796263  # OPT_PARAM: {"initial": 92.62607902796263, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.25, "type": "float"}
    order_multiplier = 0.95  # OPT_PARAM: {"initial": 0.95, "min": 0.95, "max": 1.15, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    expected_lead_time_demand = demand_estimate * lead_time * order_multiplier
    
    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock
    
    # Calculate order amount
    raw_order = max(0, target_position - inventory_position)
    
    # Apply smoothing
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_estimate
    
    # Apply base stock constraint
    order_amount = min(smoothed_order, max(0, base_stock - inventory_position))
    
    # Round to nearest integer
    return order_amount
