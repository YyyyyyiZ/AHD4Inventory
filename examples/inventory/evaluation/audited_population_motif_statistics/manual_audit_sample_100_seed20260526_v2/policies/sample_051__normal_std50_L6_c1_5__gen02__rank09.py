# sample_id: 051
# folder: deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r6
# distribution: normal_std50_L6_c1_5
# generation: 2
# rank_in_population_file: 9
# objective: 7995.64
# test_objective: 7874.44
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 548.5150245677041  # OPT_PARAM: {"initial": 548.5150245677041, "min": 100, "max": 800, "type": "float"}
    safety_stock = 119.0735286707627  # OPT_PARAM: {"initial": 119.0735286707627, "min": 50, "max": 200, "type": "float"}
    demand_forecast_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_weight = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.2, "type": "float"}
    holding_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate base target
    target_inventory = base_stock + safety_stock
    
    # Adjust for pipeline: reduce target when large incoming orders
    pipeline_adjustment = pipeline_weight * pipeline_orders[0] if pipeline_orders else 0
    adjusted_target = target_inventory - pipeline_adjustment
    
    # Calculate base order
    order_amount = max(0, adjusted_target - inventory_position)
    
    # Apply demand forecast adjustment
    order_amount = order_amount * demand_forecast_factor
    
    # Reduce order when on-hand inventory is high (holding cost consideration)
    if on_hand_inventory > 0:
        order_amount = order_amount * (1 - holding_weight * min(1.0, on_hand_inventory / base_stock))
    
    # Round to nearest integer
    order_amount = int(round(order_amount))
    
    return order_amount
