# sample_id: 071
# folder: deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_10_r2
# distribution: exponential_L2_c1_5
# generation: 9
# rank_in_population_file: 9
# objective: 10168.88
# test_objective: 10598.171
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 284.2684349440411  # OPT_PARAM: {"initial": 284.2684349440411, "min": 200, "max": 450, "type": "float"}
    safety_factor = 1.7620210737068769  # OPT_PARAM: {"initial": 1.7620210737068769, "min": 1.0, "max": 3.0, "type": "float"}
    smoothing_factor = 0.37959881581168164  # OPT_PARAM: {"initial": 0.37959881581168164, "min": 0.3, "max": 0.8, "type": "float"}
    pipeline_adjust = 0.35  # OPT_PARAM: {"initial": 0.35, "min": 0.1, "max": 0.6, "type": "float"}
    lost_sales_multiplier = 0.86505310919691  # OPT_PARAM: {"initial": 0.86505310919691, "min": 0.8, "max": 2.0, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Estimate demand from recent pipeline arrivals (weighted average)
    if len(pipeline_orders) >= 2:
        recent_demand_estimate = (pipeline_orders[0] * 0.7 + pipeline_orders[1] * 0.3)
    else:
        recent_demand_estimate = 0
    
    # Dynamic safety stock based on demand variability estimate
    safety_stock = base_stock * safety_factor * (1 + pipeline_adjust * (recent_demand_estimate / base_stock))
    
    # Adjust target based on lost sales penalty
    target_inventory = safety_stock * lost_sales_multiplier
    
    # Calculate order gap
    gap = target_inventory - inventory_position
    
    # Apply smoothing to avoid large order swings
    if gap > 0:
        order_amount = gap * smoothing_factor
    else:
        order_amount = 0
    
    # Round to nearest integer and ensure non-negative
    order_amount = max(0, int(round(order_amount)))
    
    return order_amount
