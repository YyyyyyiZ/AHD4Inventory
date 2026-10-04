# sample_id: 073
# folder: deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_e1-e1-e1_4_r4
# distribution: normal_std30_L6_c1_2
# generation: 5
# rank_in_population_file: 4
# objective: 2753.3
# test_objective: 2740.264
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;partial_adjustment;order_clipping
# extra_motifs: threshold_order_activation;integer_rounding;emergency_or_shortage_boost;nonlinear_gap_transform
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Dual-threshold policy with adaptive risk adjustment
    # This policy uses two distinct thresholds: one for normal operation and one for emergency
    # Risk level adapts based on pipeline volatility and recent inventory coverage
    
    # Base parameters
    normal_threshold = 800.0  # OPT_PARAM: {"initial": 800.0, "min": 200, "max": 800, "type": "float"}
    emergency_threshold = 229.69832788330328  # OPT_PARAM: {"initial": 229.69832788330328, "min": 50, "max": 300, "type": "float"}
    volatility_sensitivity = 0.9446073433321022  # OPT_PARAM: {"initial": 0.9446073433321022, "min": 0.5, "max": 3.0, "type": "float"}
    coverage_weight = 0.14167033675094412  # OPT_PARAM: {"initial": 0.14167033675094412, "min": 0.1, "max": 1.5, "type": "float"}
    order_aggressiveness = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.2, "type": "float"}
    min_order_size = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 50, "type": "float"}
    
    L = len(pipeline_orders)
    if L == 0:
        return 0
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate pipeline volatility (new structural element)
    if L > 1:
        pipeline_mean = sum(pipeline_orders) / L
        variance = sum((q - pipeline_mean) ** 2 for q in pipeline_orders) / L
        pipeline_volatility = variance ** 0.5
    else:
        pipeline_volatility = 0.0
    
    # Calculate coverage ratio (new structural element)
    # How many periods of average pipeline flow can current inventory cover?
    if pipeline_mean > 0:
        coverage_ratio = on_hand_inventory / pipeline_mean
    else:
        coverage_ratio = float('inf')
    
    # Determine risk level based on volatility and coverage (new structural element)
    # Higher volatility increases risk, lower coverage increases risk
    volatility_risk = min(1.0, pipeline_volatility / 100.0) if pipeline_volatility > 0 else 0.0
    coverage_risk = max(0.0, 1.0 - min(1.0, coverage_ratio / 3.0))
    
    combined_risk = (volatility_risk * volatility_sensitivity + coverage_risk * coverage_weight) / 2.0
    risk_level = min(1.0, max(0.0, combined_risk))
    
    # Adjust threshold based on risk level (new structural element)
    # Higher risk → lower threshold to be more conservative
    risk_adjustment = 1.0 - risk_level
    adjusted_threshold = emergency_threshold + (normal_threshold - emergency_threshold) * risk_adjustment
    
    # Calculate order gap
    gap = adjusted_threshold - inventory_position
    
    # Apply order aggressiveness
    if gap > min_order_size:
        order_amount = gap * order_aggressiveness
        order_amount = max(0, int(order_amount + 0.5))
    else:
        order_amount = 0
    
    return order_amount
