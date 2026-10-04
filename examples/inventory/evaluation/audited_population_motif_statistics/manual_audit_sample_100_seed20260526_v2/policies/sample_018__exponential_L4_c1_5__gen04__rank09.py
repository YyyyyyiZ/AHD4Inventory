# sample_id: 018
# folder: deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_10_r1
# distribution: exponential_L4_c1_5
# generation: 4
# rank_in_population_file: 9
# objective: 11188.91926
# test_objective: 11348.70347
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;order_up_to;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 354.2408066643192  # OPT_PARAM: {"initial": 354.2408066643192, "min": 200, "max": 600, "type": "float"}
    safety_stock = 59.47477215640345  # OPT_PARAM: {"initial": 59.47477215640345, "min": 0, "max": 150, "type": "float"}
    demand_estimate = 119.23299630310831  # OPT_PARAM: {"initial": 119.23299630310831, "min": 80, "max": 200, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.3, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected shortfall
    shortfall = max(0, base_stock - inventory_position)
    
    # Adjust for pipeline coverage
    pipeline_coverage = sum(pipeline_orders)
    expected_pipeline_needs = demand_estimate * len(pipeline_orders)
    pipeline_adjustment = max(0, expected_pipeline_needs - pipeline_coverage) * pipeline_weight
    
    # Smooth the order amount to avoid large fluctuations
    smoothed_shortfall = shortfall * smoothing_factor + safety_stock
    
    # Final order amount
    order_amount = max(0, smoothed_shortfall + pipeline_adjustment)
    
    return order_amount
