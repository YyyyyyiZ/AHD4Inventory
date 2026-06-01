# sample_id: 087
# folder: deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_no_15_default_m2_10_r1
# distribution: normal_std30_L6_c1_2
# generation: 3
# rank_in_population_file: 7
# objective: 5738.58
# test_objective: 5747.539
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;order_up_to
# extra_motifs: safety_stock_buffer
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 350  # OPT_PARAM: {'initial': 350, 'min': 10, 'max': 1000, 'type': 'float'}
    safety_stock = 50  # OPT_PARAM: {'initial': 50, 'min': 0, 'max': 200, 'type': 'float'}
    
    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)
    
    # Order up to base_stock, but ensure at least safety_stock coverage for lead time
    order_amount = max(0, base_stock - net_inventory)
    
    # Adjust order to maintain minimum safety stock
    if net_inventory + order_amount < safety_stock:
        order_amount = max(0, safety_stock - net_inventory)
    
    return order_amount
