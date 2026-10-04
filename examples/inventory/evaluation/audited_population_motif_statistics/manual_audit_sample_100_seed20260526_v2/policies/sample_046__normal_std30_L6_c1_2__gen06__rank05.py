# sample_id: 046
# folder: deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_e1-m2_6_r1
# distribution: normal_std30_L6_c1_2
# generation: 6
# rank_in_population_file: 5
# objective: 2345.88
# test_objective: 2339.654
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding;emergency_or_shortage_boost
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Core inventory parameters
    base_stock = 536.8920410178813  # OPT_PARAM: {"initial": 536.8920410178813, "min": 300, "max": 800, "type": "float"}
    safety_stock = 20.756009431915693  # OPT_PARAM: {"initial": 20.756009431915693, "min": 20, "max": 150, "type": "float"}
    
    # Cost-aware adjustment parameters
    holding_weight = 0.8160040850045172  # OPT_PARAM: {"initial": 0.8160040850045172, "min": 0.1, "max": 2.0, "type": "float"}
    shortage_weight = 2.134635819833547  # OPT_PARAM: {"initial": 2.134635819833547, "min": 0.1, "max": 3.0, "type": "float"}
    
    # Calculate total pipeline inventory (unweighted sum)
    total_pipeline = sum(pipeline_orders)
    
    # Calculate current inventory position
    current_position = on_hand_inventory + total_pipeline
    
    # Calculate target inventory position
    target_position = base_stock + safety_stock
    
    # Calculate imbalance
    imbalance = target_position - current_position
    
    # Apply cost-aware adjustment based on imbalance direction
    if imbalance > 0:
        # Risk of shortage - apply shortage weight
        adjusted_order = imbalance * shortage_weight
    else:
        # Risk of excess inventory - apply holding weight
        adjusted_order = imbalance * holding_weight
    
    # Simple smoothing based on recent demand pattern
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    if len(pipeline_orders) >= 2:
        recent_avg = (pipeline_orders[0] + pipeline_orders[1]) / 2.0
        smoothed_order = adjusted_order * smoothing_factor + recent_avg * (1 - smoothing_factor)
    else:
        smoothed_order = adjusted_order
    
    # Ensure non-negative and round to integer
    order_amount = max(0, int(round(smoothed_order)))
    
    return order_amount
