# sample_id: 054
# folder: deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r9
# distribution: normal_std30_L6_c1_5
# generation: 7
# rank_in_population_file: 8
# objective: 4044.71097
# test_objective: 3960.15521
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;partial_adjustment
# extra_motifs: safety_stock_buffer
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 686.812636924258  # OPT_PARAM: {"initial": 686.812636924258, "min": 600, "max": 850, "type": "float"}
    safety_stock = 89.54758273145202  # OPT_PARAM: {"initial": 89.54758273145202, "min": 80, "max": 140, "type": "float"}
    pipeline_coverage = 0.8624625103570247  # OPT_PARAM: {"initial": 0.8624625103570247, "min": 0.7, "max": 1.0, "type": "float"}
    demand_multiplier = 1.0420790590982434  # OPT_PARAM: {"initial": 1.0420790590982434, "min": 1.0, "max": 1.3, "type": "float"}
    smoothing_factor = 0.15029012827558405  # OPT_PARAM: {"initial": 0.15029012827558405, "min": 0.1, "max": 0.5, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate effective pipeline coverage
    pipeline_sum = sum(pipeline_orders)
    effective_pipeline = pipeline_sum * pipeline_coverage
    
    # Calculate target inventory level
    target_inventory = base_stock + safety_stock
    
    # Calculate order amount with smoothing
    raw_order = max(0, target_inventory - inventory_position + effective_pipeline)
    
    # Apply demand multiplier and smoothing
    order_amount = raw_order * demand_multiplier * smoothing_factor
    
    # Round to nearest integer
    return order_amount
