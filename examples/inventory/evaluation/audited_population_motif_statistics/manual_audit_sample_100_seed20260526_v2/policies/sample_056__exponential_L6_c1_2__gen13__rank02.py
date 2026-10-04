# sample_id: 056
# folder: deepseek-chat_exponential_L6_c1_2_50_plain_processed_no_15_default_m2_10_r1
# distribution: exponential_L6_c1_2
# generation: 13
# rank_in_population_file: 2
# objective: 7244.18
# test_objective: 7383.881
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;order_up_to
# extra_motifs: safety_stock_buffer
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 290  # OPT_PARAM: {'initial': 290, 'min': 10, 'max': 1000, 'type': 'float'}
    safety_stock = 60  # OPT_PARAM: {'initial': 60, 'min': 0, 'max': 200, 'type': 'float'}
    
    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)
    
    # Order up to base_stock plus safety_stock adjustment
    order_amount = max(0, base_stock + safety_stock - net_inventory)
    
    return order_amount
