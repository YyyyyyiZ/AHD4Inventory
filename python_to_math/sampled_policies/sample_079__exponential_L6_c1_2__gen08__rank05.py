# sample_id: 079
# folder: grok-4.1-fast_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r1
# distribution: exponential_L6_c1_2
# generation: 8
# rank_in_population_file: 5
# objective: 6193.19816
# test_objective: 6337.68845
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: pipeline_weighting;order_up_to
# extra_motifs: 
def compute_order_amount(on_hand_inventory, pipeline_orders):
    bs = 252.76461729338735  # OPT_PARAM: {"initial": 252.76461729338735, "min": 50.0, "max": 1000.0, "type": "float"}
    w_i = 0.06301367498820724  # OPT_PARAM: {"initial": 0.06301367498820724, "min": 0.0, "max": 2.0, "type": "float"}
    w_pipe = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}
    discount = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.8, "max": 1.2, "type": "float"}
    ip = w_i * on_hand_inventory
    w = w_pipe
    for q in pipeline_orders:
        ip += w * q
        w *= discount
    order_amount = max(0.0, bs - ip)
    return order_amount
