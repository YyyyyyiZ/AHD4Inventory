# sample_id: 057
# folder: deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r6
# distribution: normal_std10_L6_c1_5
# generation: 5
# rank_in_population_file: 1
# objective: 1318.78
# test_objective: 1311.369
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;threshold_order_activation;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 589.9262169191956  # OPT_PARAM: {"initial": 589.9262169191956, "min": 450, "max": 700, "type": "float"}
    safety_stock = 104.7989098814106  # OPT_PARAM: {"initial": 104.7989098814106, "min": 40, "max": 120, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.9, "type": "float"}
    demand_adjustment = 0.9404108089646986  # OPT_PARAM: {"initial": 0.9404108089646986, "min": 0.8, "max": 3.0, "type": "float"}
    min_order = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 10, "max": 50, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate demand estimate using all pipeline orders (better signal)
    if len(pipeline_orders) > 0:
        # Weight recent orders more heavily
        weights = [0.4, 0.3, 0.2, 0.1, 0.0, 0.0][:len(pipeline_orders)]
        weighted_sum = sum(w * q for w, q in zip(weights, pipeline_orders))
        weight_sum = sum(weights[:len(pipeline_orders)])
        demand_estimate = weighted_sum / weight_sum if weight_sum > 0 else 100.0
    else:
        demand_estimate = 100.0
    
    # Adjust base stock based on demand estimate
    adjusted_base = base_stock + (demand_estimate - 100) * demand_adjustment
    
    # Calculate target inventory position
    target_position = adjusted_base + safety_stock
    
    # Calculate order needed
    order_needed = target_position - inventory_position
    
    # Apply smoothing only when ordering
    if order_needed > min_order:
        smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * demand_estimate
    else:
        smoothed_order = max(0, order_needed)
    
    # Round to integer and ensure non-negative
    order_amount = max(0, int(round(smoothed_order)))
    
    return order_amount
