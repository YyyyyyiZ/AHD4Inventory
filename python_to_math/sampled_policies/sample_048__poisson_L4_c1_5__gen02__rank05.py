# sample_id: 048
# folder: deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_10_r1
# distribution: poisson_L4_c1_5
# generation: 2
# rank_in_population_file: 5
# objective: 2183.7834
# test_objective: 2221.19349
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment;order_smoothing
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 522.6543634227193  # OPT_PARAM: {"initial": 522.6543634227193, "min": 300, "max": 700, "type": "float"}
    safety_stock = 142.99766910765004  # OPT_PARAM: {"initial": 142.99766910765004, "min": 20, "max": 150, "type": "float"}
    demand_forecast = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.2, "max": 0.8, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 1.0, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)
    
    # Calculate target inventory level with adjusted safety stock
    target_inventory = expected_lead_time_demand + safety_stock
    
    # Use minimum of base_stock and target_inventory to avoid over-ordering
    order_up_to = min(base_stock, target_inventory)
    
    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)
    
    # Apply smoothing with pipeline consideration
    if pipeline_orders:
        # Weight recent pipeline orders more heavily
        weighted_pipeline = pipeline_weight * pipeline_orders[-1] + (1 - pipeline_weight) * pipeline_orders[0]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * weighted_pipeline
    else:
        smoothed_order = order_amount
    
    # Round to nearest integer for practical ordering
    return order_amount
