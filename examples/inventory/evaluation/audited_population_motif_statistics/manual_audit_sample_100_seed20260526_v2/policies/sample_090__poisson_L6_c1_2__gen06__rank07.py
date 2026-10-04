# sample_id: 090
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_no_15_default_m2_10_r1
# distribution: poisson_L6_c1_2
# generation: 6
# rank_in_population_file: 7
# objective: 3317.3
# test_objective: 3309.643
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;order_up_to
# extra_motifs: safety_stock_buffer
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 550  # OPT_PARAM: {'initial': 550, 'min': 10, 'max': 1000, 'type': 'float'}
    safety_stock = 30  # OPT_PARAM: {'initial': 30, 'min': 0, 'max': 200, 'type': 'float'}
    
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    target_inventory = base_stock + safety_stock
    
    order_amount = max(0, target_inventory - inventory_position)
    return order_amount
