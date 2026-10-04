# sample_id: 015
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1
# distribution: poisson_L6_c1_2
# generation: 1
# rank_in_population_file: 3
# objective: 2785.04
# test_objective: 2787.582
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;state_dependent_target
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 637.9351014652013  # OPT_PARAM: {"initial": 637.9351014652013, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 23.945552227041272  # OPT_PARAM: {"initial": 23.945552227041272, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0
    
    # Adjust base stock based on recent demand pattern
    adjusted_base = base_stock + (avg_recent_demand - 100) * smoothing_factor
    
    # Calculate target inventory position
    target_position = adjusted_base + safety_stock
    
    # Calculate order amount with smoothing
    raw_order = max(0, target_position - inventory_position)
    order_amount = int(round(raw_order))
    
    return order_amount
