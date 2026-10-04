# sample_id: 045
# folder: grok-4.1-fast_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r1
# distribution: poisson_L6_c1_2
# generation: 1
# rank_in_population_file: 6
# objective: 2781.10132
# test_objective: 2783.54765
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus
def compute_order_amount(on_hand_inventory, pipeline_orders):
    L = 6
    lookback_k = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 6, "type": "int"}
    prior_mu = 102.48823456990216  # OPT_PARAM: {"initial": 102.48823456990216, "min": 80, "max": 120, "type": "float"}
    prior_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.0, "max": 1.0, "type": "float"}
    safety_stock = 49.06507394056868  # OPT_PARAM: {"initial": 49.06507394056868, "min": 0.0, "max": 100.0, "type": "float"}
    recent_orders = pipeline_orders[-lookback_k:]
    recent_avg = sum(recent_orders) / lookback_k
    blended_mu = prior_weight * prior_mu + (1 - prior_weight) * recent_avg
    lt_forecast = blended_mu * L
    base_stock = lt_forecast + safety_stock
    total_ip = on_hand_inventory + sum(pipeline_orders)
    order_amount = max(0, base_stock - total_ip)
    return order_amount
