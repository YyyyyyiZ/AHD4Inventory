# sample_id: 088
# folder: deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r6
# distribution: poisson_L2_c1_2
# generation: 3
# rank_in_population_file: 2
# objective: 782.0
# test_objective: 790.83
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;order_up_to;partial_adjustment;order_smoothing
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 259.96374132943953  # OPT_PARAM: {"initial": 259.96374132943953, "min": 100, "max": 400, "type": "float"}
    safety_stock = 34.96374132943884  # OPT_PARAM: {"initial": 34.96374132943884, "min": 0, "max": 100, "type": "float"}
    smoothing_factor = 0.2206775028960104  # OPT_PARAM: {"initial": 0.2206775028960104, "min": 0.1, "max": 0.8, "type": "float"}
    
    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)
    
    # Simple base-stock policy with smoothing
    raw_order = max(0, base_stock + safety_stock - net_inventory)
    
    # Apply smoothing using recent order if available
    if len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * recent_order
    else:
        smoothed_order = raw_order
    
    # Round to nearest integer
    order_amount = int(round(smoothed_order))
    
    return order_amount
