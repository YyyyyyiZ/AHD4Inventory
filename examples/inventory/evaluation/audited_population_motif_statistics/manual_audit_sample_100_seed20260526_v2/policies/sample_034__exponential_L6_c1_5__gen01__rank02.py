# sample_id: 034
# folder: deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6
# distribution: exponential_L6_c1_5
# generation: 1
# rank_in_population_file: 2
# objective: 12927.64416
# test_objective: 13114.4267
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;order_up_to
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 477.5417156010887  # OPT_PARAM: {"initial": 477.5417156010887, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 77.1165950245596  # OPT_PARAM: {"initial": 77.1165950245596, "min": 50, "max": 400, "type": "float"}
    demand_estimate = 72.05912542391138  # OPT_PARAM: {"initial": 72.05912542391138, "min": 50, "max": 300, "type": "float"}
    pipeline_weight = 0.9975758916253765  # OPT_PARAM: {"initial": 0.9975758916253765, "min": 0.1, "max": 1.5, "type": "float"}
    
    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline
    
    # Calculate target inventory level
    target_inventory = base_stock + safety_stock
    
    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)
    
    # Add demand estimate adjustment
    order_amount = max(order_amount, demand_estimate - sum(pipeline_orders[-2:]) if len(pipeline_orders) >= 2 else demand_estimate)
    
    return order_amount
