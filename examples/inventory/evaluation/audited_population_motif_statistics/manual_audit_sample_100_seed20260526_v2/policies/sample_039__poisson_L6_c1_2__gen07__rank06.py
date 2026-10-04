# sample_id: 039
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_e1-m2_6_r1
# distribution: poisson_L6_c1_2
# generation: 7
# rank_in_population_file: 6
# objective: 914.48
# test_objective: 901.753
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;order_up_to;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;threshold_order_activation;integer_rounding;nonlinear_gap_transform
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Base stock level
    base_stock = 645.7134146565843  # OPT_PARAM: {"initial": 645.7134146565843, "min": 400, "max": 1000, "type": "float"}
    
    # Demand forecasting parameters
    forecast_horizon = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 6, "type": "int"}
    forecast_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    
    # Pipeline risk assessment parameters
    risk_threshold = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.5, "type": "float"}
    risk_multiplier = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.0, "max": 3.0, "type": "float"}
    
    # Order smoothing parameters
    smooth_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    min_order = 5  # OPT_PARAM: {"initial": 5, "min": 0, "max": 20, "type": "int"}
    
    L = len(pipeline_orders)
    
    # 1. Demand forecasting from pipeline pattern
    # Use pipeline orders as proxy for future demand (since they reflect past ordering decisions)
    if L >= forecast_horizon:
        # Extract recent pipeline orders for forecasting
        recent_pipeline = pipeline_orders[-forecast_horizon:] if forecast_horizon > 0 else []
        if recent_pipeline:
            # Weighted average with more weight on recent periods
            weights = [0.5 ** (forecast_horizon - i - 1) for i in range(forecast_horizon)]
            weight_sum = sum(weights)
            forecast_demand = sum(q * w for q, w in zip(recent_pipeline, weights)) / weight_sum
        else:
            forecast_demand = 0
    else:
        forecast_demand = sum(pipeline_orders) / L if L > 0 else 0
    
    # 2. Pipeline risk assessment
    # Calculate pipeline variability as risk indicator
    if L > 1:
        pipeline_mean = sum(pipeline_orders) / L
        pipeline_variance = sum((q - pipeline_mean) ** 2 for q in pipeline_orders) / L
        pipeline_std = pipeline_variance ** 0.5
        
        # Normalized risk measure (0 to 1)
        if pipeline_mean > 0:
            risk_level = min(1.0, pipeline_std / pipeline_mean)
        else:
            risk_level = 0
    else:
        risk_level = 0
    
    # 3. Dynamic safety stock based on pipeline risk
    base_safety_stock = 27.91616435187665  # OPT_PARAM: {"initial": 27.91616435187665, "min": 10, "max": 150, "type": "float"}
    
    if risk_level > risk_threshold:
        safety_stock = base_safety_stock * 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.9, "type": "float"}
    else:
        # Linear interpolation between base and reduced safety stock
        safety_reduction = (risk_threshold - risk_level) / risk_threshold
        safety_stock = base_safety_stock * (1.0 - 0.5 * safety_reduction)
    
    # 4. Calculate inventory position with forecast adjustment
    simple_inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Adjust inventory position based on demand forecast
    # If forecast is high, effectively reduce perceived inventory
    forecast_adjustment = forecast_demand * forecast_weight
    adjusted_inventory_position = simple_inventory_position - forecast_adjustment
    
    # 5. Calculate target with dynamic safety stock
    target_position = base_stock + safety_stock
    
    # 6. Calculate raw order amount
    raw_order = max(0, target_position - adjusted_inventory_position)
    
    # 7. Apply smoothing to avoid drastic order changes
    # Use pipeline average as reference for smoothing
    if L > 0:
        pipeline_avg = sum(pipeline_orders) / L
        smoothed_order = smooth_factor * raw_order + (1 - smooth_factor) * pipeline_avg
    else:
        smoothed_order = raw_order
    
    # 8. Apply minimum order constraint
    if smoothed_order > 0:
        order_amount = max(min_order, int(round(smoothed_order)))
    else:
        order_amount = 0
    
    return order_amount
