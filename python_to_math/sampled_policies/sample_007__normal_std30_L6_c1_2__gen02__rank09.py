# sample_id: 007
# folder: deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2plural_6_r6
# distribution: normal_std30_L6_c1_2
# generation: 2
# rank_in_population_file: 9
# objective: 4301.9
# test_objective: 4257.044
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;order_up_to
# extra_motifs: safety_stock_buffer;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 594.9887769151144  # OPT_PARAM: {"initial": 594.9887769151144, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.00013241732881  # OPT_PARAM: {"initial": 50.00013241732881, "min": 0, "max": 200, "type": "float"}
    pipeline_factor = 1.1195224967701995  # OPT_PARAM: {"initial": 1.1195224967701995, "min": 0.5, "max": 1.2, "type": "float"}
    
    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_factor
    inventory_position = on_hand_inventory + effective_pipeline
    
    # Adjust base stock based on safety stock
    adjusted_base_stock = base_stock + safety_stock
    
    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)
    
    # Round to nearest integer since order amount should be integer
    order_amount = int(round(order_amount))
    
    return order_amount
