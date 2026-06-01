# sample_id: 021
# folder: deepseek-chat_exponential_L6_c1_2_50_plain_processed_no_15_default_m2_10_r1
# distribution: exponential_L6_c1_2
# generation: 18
# rank_in_population_file: 1
# objective: 7242.76
# test_objective: 7384.309
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;order_up_to
# extra_motifs: safety_stock_buffer
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 310  # OPT_PARAM: {'initial': 310, 'min': 10, 'max': 1000, 'type': 'float'}
    safety_stock = 45  # OPT_PARAM: {'initial': 45, 'min': 0, 'max': 200, 'type': 'float'}
    
    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)
    
    # Order up to base_stock plus safety_stock adjustment
    order_amount = max(0, base_stock + safety_stock - net_inventory)
    
    return order_amount
