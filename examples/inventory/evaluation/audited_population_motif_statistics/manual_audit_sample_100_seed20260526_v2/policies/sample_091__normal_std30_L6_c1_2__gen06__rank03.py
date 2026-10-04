# sample_id: 091
# folder: deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_e2-e2-e2_4_r3
# distribution: normal_std30_L6_c1_2
# generation: 6
# rank_in_population_file: 3
# objective: 3639.88
# test_objective: 3641.658
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding;nonlinear_gap_transform
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 595.3256931543754  # OPT_PARAM: {"initial": 595.3256931543754, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.79935343897438  # OPT_PARAM: {"initial": 50.79935343897438, "min": 0, "max": 200, "type": "float"}
    order_floor = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 100, "type": "int"}
    order_ceiling = 300  # OPT_PARAM: {"initial": 300, "min": 50, "max": 500, "type": "int"}
    demand_forecast_factor = 0.6218666867485925  # OPT_PARAM: {"initial": 0.6218666867485925, "min": 0.1, "max": 2.0, "type": "float"}
    pipeline_weight_factor = 0.36734933385589097  # OPT_PARAM: {"initial": 0.36734933385589097, "min": 0.0, "max": 1.0, "type": "float"}
    demand_smoothing_factor = 0.6473587686473684  # OPT_PARAM: {"initial": 0.6473587686473684, "min": 0.0, "max": 1.0, "type": "float"}
    safety_stock_multiplier = 1.2216292069395431  # OPT_PARAM: {"initial": 1.2216292069395431, "min": 0.5, "max": 3.0, "type": "float"}
    demand_variability_factor = 0.23499331893006076  # OPT_PARAM: {"initial": 0.23499331893006076, "min": 0.0, "max": 2.0, "type": "float"}
    pipeline_decay_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.1, "max": 1.0, "type": "float"}
    on_hand_sensitivity = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    pipeline_std_factor = 0.0036084261964755057  # OPT_PARAM: {"initial": 0.0036084261964755057, "min": 0.0, "max": 0.5, "type": "float"}
    
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand using exponential smoothing of recent pipeline arrivals
    if len(pipeline_orders) >= 3:
        recent_arrivals = pipeline_orders[:3]
        # Apply exponential smoothing weights
        weights = [demand_smoothing_factor ** i for i in range(len(recent_arrivals))]
        weights = [w / sum(weights) for w in weights]
        smoothed_demand = sum(w * d for w, d in zip(weights, recent_arrivals))
        
        # Calculate variability in recent arrivals
        avg_recent = sum(recent_arrivals) / len(recent_arrivals)
        squared_diffs = [(x - avg_recent) ** 2 for x in recent_arrivals]
        variability = (sum(squared_diffs) / len(recent_arrivals)) ** 0.5
        
        # Combine smoothed demand with variability adjustment
        expected_demand = smoothed_demand * demand_forecast_factor + variability * demand_variability_factor
    else:
        expected_demand = 100.0 * demand_forecast_factor
    
    # Calculate pipeline-weighted adjustment with exponential decay
    pipeline_adjustment = 0
    for i, order in enumerate(pipeline_orders):
        decay = pipeline_decay_factor ** i
        pipeline_adjustment += order * decay * pipeline_weight_factor
    
    # Calculate pipeline variability adjustment using all pipeline orders
    if len(pipeline_orders) >= 2:
        pipeline_mean = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_variance = sum((q - pipeline_mean) ** 2 for q in pipeline_orders) / len(pipeline_orders)
        pipeline_std = max(0, pipeline_variance ** 0.5)
        variability_adjustment = pipeline_std * pipeline_std_factor
    else:
        variability_adjustment = 0.0
    
    # Dynamic safety stock adjustment
    dynamic_safety = safety_stock * safety_stock_multiplier
    
    # On-hand inventory adjustment (reduces order when on-hand is high)
    on_hand_adjustment = on_hand_inventory * on_hand_sensitivity
    
    # Calculate order-up-to level with all adjustments
    order_up_to = base_stock + dynamic_safety + expected_demand - pipeline_adjustment + variability_adjustment - on_hand_adjustment
    
    # Base order amount
    raw_order = max(0, order_up_to - inventory_position)
    
    # Apply floor and ceiling constraints
    constrained_order = max(order_floor, min(order_ceiling, raw_order))
    
    # Round to nearest integer
    order_amount = int(round(constrained_order))
    
    return order_amount
