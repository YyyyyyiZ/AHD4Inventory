# sample_id: 022
# folder: deepseek-chat_normal_std50_L2_c1_5_50_plain_processed_scipy_15_default_e1-e2-m2_2_r1
# distribution: normal_std50_L2_c1_5
# generation: 0
# rank_in_population_file: 1
# objective: 5738.975
# test_objective: 5705.41496
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;order_up_to
# extra_motifs: 
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 345.92500000000797  # OPT_PARAM: {"initial": 345.92500000000797, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
