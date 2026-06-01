# sample_id: 011
# folder: deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2plural_2_r6
# distribution: exponential_L6_c1_5
# generation: 7
# rank_in_population_file: 2
# objective: 11107.66
# test_objective: 11209.965
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 564.7744400524856  # OPT_PARAM: {"initial": 564.7744400524856, "min": 400, "max": 800, "type": "float"}
    safety_stock = 104.87444005248125  # OPT_PARAM: {"initial": 104.87444005248125, "min": 50, "max": 250, "type": "float"}
    lead_time = len(pipeline_orders)
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time using recent arrivals
    # Use first 3 pipeline orders (recently arrived) as proxy for demand
    if len(pipeline_orders) >= 3:
        recent_demand = pipeline_orders[0] + pipeline_orders[1] + pipeline_orders[2]
        avg_recent_demand = recent_demand / 3.0
    else:
        avg_recent_demand = sum(pipeline_orders) / max(len(pipeline_orders), 1)
    
    # Dynamic adjustment based on recent demand
    demand_adjustment_factor = 0.7326478951298112  # OPT_PARAM: {"initial": 0.7326478951298112, "min": 0.3, "max": 1.5, "type": "float"}
    demand_adjustment = avg_recent_demand * lead_time * demand_adjustment_factor
    
    # Calculate target inventory position
    target_position = base_stock + safety_stock + demand_adjustment
    
    # Calculate raw order needed
    raw_order = max(0, target_position - inventory_position)
    
    # Apply aggressive smoothing to prevent over-ordering
    smoothing_factor = 0.16978525457711363  # OPT_PARAM: {"initial": 0.16978525457711363, "min": 0.1, "max": 0.5, "type": "float"}
    smoothed_order = smoothing_factor * raw_order
    
    # Round to nearest integer
    order_amount = int(round(smoothed_order))
    
    return order_amount
