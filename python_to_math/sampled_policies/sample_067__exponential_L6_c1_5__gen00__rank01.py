# sample_id: 067
# folder: deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2plural_2_r6
# distribution: exponential_L6_c1_5
# generation: 0
# rank_in_population_file: 1
# objective: 13069.62249
# test_objective: 13284.31768
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;order_up_to
# extra_motifs: 
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 553.9875397341209  # OPT_PARAM: {"initial": 553.9875397341209, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
