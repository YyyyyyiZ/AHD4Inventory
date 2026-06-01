# sample_id: 097
# folder: deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_e1-e1-e1_4_r1
# distribution: normal_std30_L6_c1_2
# generation: 4
# rank_in_population_file: 3
# objective: 2418.7
# test_objective: 2373.232
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;order_up_to;partial_adjustment;order_clipping
# extra_motifs: pipeline_demand_proxy;near_term_pipeline_focus;threshold_order_activation;integer_rounding;emergency_or_shortage_boost;nonlinear_gap_transform
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Base stock level
    base_stock = 548.2459833585183  # OPT_PARAM: {"initial": 548.2459833585183, "min": 300, "max": 800, "type": "float"}
    
    # Newsvendor critical ratio adjustment factor
    newsvendor_factor = 0.49066732315215933  # OPT_PARAM: {"initial": 0.49066732315215933, "min": 0.1, "max": 2.0, "type": "float"}
    
    # Pipeline imbalance penalty factor
    imbalance_penalty = 0.29801229754657366  # OPT_PARAM: {"initial": 0.29801229754657366, "min": 0.0, "max": 1.0, "type": "float"}
    
    # Lead time urgency factor
    urgency_factor = 0.22256734330247824  # OPT_PARAM: {"initial": 0.22256734330247824, "min": 0.0, "max": 1.0, "type": "float"}
    
    # Order smoothing factor
    smoothing = 0.1374992000765368  # OPT_PARAM: {"initial": 0.1374992000765368, "min": 0.0, "max": 1.0, "type": "float"}
    
    # NOVEL FEATURE: Newsvendor-inspired critical ratio adjustment
    # Calculate optimal service level based on cost ratio p/(h+p) = 2/3
    critical_ratio = 2.0 / (1.0 + 2.0)  # p/(h+p) = 2/3
    # Adjust base stock using newsvendor logic scaled by factor
    newsvendor_adjusted_base = base_stock * (1.0 + newsvendor_factor * (critical_ratio - 0.5))
    
    L = len(pipeline_orders)
    if L == 0:
        return int(round(newsvendor_adjusted_base - on_hand_inventory))
    
    total_pipeline = sum(pipeline_orders)
    
    # NOVEL FEATURE: Lead-time-weighted pipeline coverage analysis
    # Calculate coverage for each lead time period
    coverage_deficit = 0.0
    cumulative_inventory = on_hand_inventory
    
    for k in range(L):
        # Inventory available by period t+k
        if k == 0:
            # Current period: on-hand + arriving order
            available = cumulative_inventory + pipeline_orders[0]
        else:
            # Future periods: add pipeline orders arriving at that period
            available = cumulative_inventory + pipeline_orders[k]
        
        # Expected demand coverage needed (using base stock as proxy for average demand)
        expected_coverage_needed = newsvendor_adjusted_base * (k + 1) / L
        
        # Deficit if available inventory is less than needed coverage
        if available < expected_coverage_needed:
            # Weight deficit by urgency (earlier periods more urgent)
            urgency_weight = 1.0 / (k + 1)
            deficit = (expected_coverage_needed - available) * urgency_weight
            coverage_deficit += deficit
        
        # Update cumulative inventory for next period
        if k == 0:
            cumulative_inventory = max(0, available - newsvendor_adjusted_base / L)
        else:
            cumulative_inventory = available
    
    # NOVEL FEATURE: Pipeline imbalance penalty
    # Penalize if pipeline is concentrated in certain periods
    if L > 1 and total_pipeline > 0:
        # Calculate coefficient of variation of pipeline orders
        mean_pipeline = total_pipeline / L
        if mean_pipeline > 0:
            variance = sum((q - mean_pipeline) ** 2 for q in pipeline_orders) / L
            cv = (variance ** 0.5) / mean_pipeline
            # Higher CV → more imbalance → apply penalty
            imbalance_adjustment = 1.0 - imbalance_penalty * min(cv, 2.0)
        else:
            imbalance_adjustment = 1.0
    else:
        imbalance_adjustment = 1.0
    
    # Calculate urgency adjustment based on coverage deficit
    if newsvendor_adjusted_base > 0:
        urgency_adjustment = 1.0 + urgency_factor * (coverage_deficit / newsvendor_adjusted_base)
    else:
        urgency_adjustment = 1.0
    
    # Final adjusted target
    adjusted_target = newsvendor_adjusted_base * imbalance_adjustment * urgency_adjustment
    
    # Current inventory position
    current_position = on_hand_inventory + total_pipeline
    
    # Raw order amount
    raw_order = max(0, adjusted_target - current_position)
    
    # Apply smoothing with recent pipeline average
    if L >= 2:
        recent_avg = sum(pipeline_orders[-min(3, L):]) / min(3, L)
        smoothed_order = smoothing * raw_order + (1 - smoothing) * recent_avg
    else:
        smoothed_order = raw_order
    
    # Ensure non-negative integer
    order_amount = int(round(max(0, smoothed_order)))
    
    return order_amount
