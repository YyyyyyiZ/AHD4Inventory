# sample_id: 064
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_no_15_default_m2_10_r1
# distribution: poisson_L6_c1_2
# generation: 7
# rank_in_population_file: 4
# objective: 3001.4
# test_objective: 2994.197
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;order_up_to
# extra_motifs: safety_stock_buffer
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 510  # OPT_PARAM: {'initial': 510, 'min': 10, 'max': 1000, 'type': 'float'}
    safety_stock = 110  # OPT_PARAM: {'initial': 110, 'min': 0, 'max': 200, 'type': 'float'}
    
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    target_inventory = base_stock + safety_stock
    
    order_amount = max(0, target_inventory - inventory_position)
    return order_amount
