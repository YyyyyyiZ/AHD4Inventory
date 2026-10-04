# sample_id: 093
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_10_r1
# distribution: poisson_L6_c1_2
# generation: 7
# rank_in_population_file: 9
# objective: 781.99954
# test_objective: 757.87781
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;order_clipping
# extra_motifs: safety_stock_buffer;near_term_pipeline_focus
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Fixed dataset constants
    d_hat = 100.0  # mean demand
    L = len(pipeline_orders)
    
    # Optimizable parameters
    base_order = 89.31822339686998  # OPT_PARAM: {"initial": 89.31822339686998, "min": 80.0, "max": 110.0, "type": "float"}
    inv_feedback = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.3, "type": "float"}
    pipeline_feedback = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.2, "type": "float"}
    shortfall_gain = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    pipeline_shape_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.3, "type": "float"}
    safety_buffer = 5.687000958575839  # OPT_PARAM: {"initial": 5.687000958575839, "min": 0.0, "max": 20.0, "type": "float"}
    target_coverage = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 6, "type": "int"}
    
    # Core features
    available_now = on_hand_inventory + pipeline_orders[0]
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Pipeline shape features - focus on near-term vs far-term balance
    if L > 0:
        # Next target_coverage periods vs rest of pipeline
        near_term = sum(pipeline_orders[:min(target_coverage, L)])
        far_term = sum(pipeline_orders[target_coverage:]) if L > target_coverage else 0
        
        # Normalize for fair comparison
        near_term_norm = near_term / float(target_coverage) if L >= target_coverage else near_term / L
        far_term_norm = far_term / max(1, L-target_coverage) if L > target_coverage else 0
        
        # Shape indicator: positive if near-term is heavier than far-term
        pipeline_shape = near_term_norm - far_term_norm
    else:
        pipeline_shape = 0.0
    
    # Projected shortfall over next target_coverage periods
    projected_shortfall = 0.0
    for m in range(1, min(target_coverage+1, L+1)):
        projected_inv = on_hand_inventory + sum(pipeline_orders[:m]) - m * d_hat
        projected_shortfall += max(0, -projected_inv)
    
    # Core order calculation
    # 1. Base constant order with safety buffer
    base = base_order + safety_buffer
    
    # 2. Inventory feedback (negative feedback on high inventory)
    inv_adjust = -inv_feedback * on_hand_inventory
    
    # 3. Pipeline feedback (negative feedback on total pipeline)
    pipe_adjust = -pipeline_feedback * sum(pipeline_orders)
    
    # 4. Shortfall compensation
    shortfall_adjust = shortfall_gain * projected_shortfall / float(target_coverage)
    
    # 5. Pipeline shape adjustment
    shape_adjust = -pipeline_shape_weight * pipeline_shape
    
    # Combine adjustments
    raw_order = base + inv_adjust + pipe_adjust + shortfall_adjust + shape_adjust
    
    # Ensure non-negative and reasonable magnitude
    order_amount = max(0.0, min(raw_order, 2.0 * base_order))
    
    # Round to nearest integer
    return order_amount
