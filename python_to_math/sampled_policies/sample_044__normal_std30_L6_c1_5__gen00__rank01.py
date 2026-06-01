# sample_id: 044
# folder: deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r7
# distribution: normal_std30_L6_c1_5
# generation: 0
# rank_in_population_file: 1
# objective: 6033.8008
# test_objective: 5897.01244
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;order_up_to
# extra_motifs: 
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 692.0049957614882  # OPT_PARAM: {"initial": 692.0049957614882, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
