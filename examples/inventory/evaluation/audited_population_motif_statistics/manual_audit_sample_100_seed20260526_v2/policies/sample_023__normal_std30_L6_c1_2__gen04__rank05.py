# sample_id: 023
# folder: deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_no_15_default_m2_10_r1
# distribution: normal_std30_L6_c1_2
# generation: 4
# rank_in_population_file: 5
# objective: 4885.1
# test_objective: 4872.183
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;order_up_to
# extra_motifs: 
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450  # OPT_PARAM: {'initial': 450, 'min': 10, 'max': 1000, 'type': 'float'}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
