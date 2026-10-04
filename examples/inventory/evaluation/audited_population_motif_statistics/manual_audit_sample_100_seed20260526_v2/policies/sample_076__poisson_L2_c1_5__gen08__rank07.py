# sample_id: 076
# folder: deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_10_r1
# distribution: poisson_L2_c1_5
# generation: 8
# rank_in_population_file: 7
# objective: 1116.9
# test_objective: 1093.328
# is_top10_by_distribution: True
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 310.17160011102334  # OPT_PARAM: {"initial": 310.17160011102334, "min": 250, "max": 320, "type": "float"}
    safety_stock = 63.44756030622884  # OPT_PARAM: {"initial": 63.44756030622884, "min": 30, "max": 70, "type": "float"}
    adjustment_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.6, "max": 1.0, "type": "float"}
    demand_estimate = 100.01298553345889  # OPT_PARAM: {"initial": 100.01298553345889, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.4, "type": "float"}
    min_order_multiplier = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.3, "type": "float"}
    max_order_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.0, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected pipeline contribution
    expected_pipeline = sum(pipeline_orders) * pipeline_weight
    
    # Target inventory level
    target_inventory = base_stock + safety_stock - expected_pipeline
    
    # Calculate base order amount
    order_amount = max(0, (target_inventory - inventory_position) * adjustment_factor)
    
    # Apply order limits
    max_order = demand_estimate * max_order_multiplier
    min_order = demand_estimate * min_order_multiplier
    
    if order_amount > 0:
        # Ensure reasonable order sizes
        order_amount = max(min_order, min(order_amount, max_order))
    
    # Round to nearest integer
    order_amount = int(round(order_amount))
    
    return order_amount
