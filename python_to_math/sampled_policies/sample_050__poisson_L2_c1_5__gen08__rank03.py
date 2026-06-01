# sample_id: 050
# folder: deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6
# distribution: poisson_L2_c1_5
# generation: 8
# rank_in_population_file: 3
# objective: 1220.58
# test_objective: 1215.692
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;order_up_to;partial_adjustment;order_smoothing
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 291.40237332064817  # OPT_PARAM: {"initial": 291.40237332064817, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 32.420891839163716  # OPT_PARAM: {"initial": 32.420891839163716, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 1.1817895463385606  # OPT_PARAM: {"initial": 1.1817895463385606, "min": 0.1, "max": 1.5, "type": "float"}
    
    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline
    
    # Adjust base stock based on safety stock
    adjusted_base_stock = base_stock + safety_stock
    
    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)
    
    # Apply smoothing to avoid extreme order variations
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_order
        order_amount = max(0, smoothed_order)
    
    # Round to nearest integer since order amounts should be integers
    order_amount = int(round(order_amount))
    
    return order_amount
