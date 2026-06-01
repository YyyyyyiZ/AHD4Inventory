# sample_id: 069
# folder: deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_e1-e2_6_r2
# distribution: exponential_L6_c1_2
# generation: 1
# rank_in_population_file: 2
# objective: 6376.28
# test_objective: 6445.733
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: pipeline_weighting;order_up_to;partial_adjustment;order_smoothing
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;threshold_order_activation;integer_rounding;emergency_or_shortage_boost
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Base stock level - fundamental parameter
    base_stock = 326.0462767090309  # OPT_PARAM: {"initial": 326.0462767090309, "min": 100, "max": 800, "type": "float"}
    
    # Safety stock multiplier - adjusts for demand variability
    safety_multiplier = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 3.0, "type": "float"}
    
    # Pipeline weighting factor - gives more weight to imminent arrivals
    pipeline_weight = 1.044462251668397  # OPT_PARAM: {"initial": 1.044462251668397, "min": 0.1, "max": 1.5, "type": "float"}
    
    # Emergency threshold for aggressive ordering
    emergency_threshold = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 50, "max": 300, "type": "float"}
    
    # Emergency boost multiplier
    emergency_boost = 1.1712478055383213  # OPT_PARAM: {"initial": 1.1712478055383213, "min": 1.1, "max": 2.0, "type": "float"}
    
    # Calculate weighted pipeline inventory
    # More weight to orders arriving soon, less to distant ones
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_weight ** (i + 1)  # Exponential decay
        weighted_pipeline += order * weight
    
    # Calculate effective inventory position
    effective_inventory = on_hand_inventory + weighted_pipeline
    
    # Calculate demand coverage period (how many periods of average demand we want to cover)
    coverage_periods = 1.1001181735173573  # OPT_PARAM: {"initial": 1.1001181735173573, "min": 1.0, "max": 5.0, "type": "float"}
    
    # Estimate average demand from pipeline pattern (assuming recent orders reflect demand)
    if sum(pipeline_orders) > 0:
        avg_estimated_demand = 99.10971369816312  # Optimized
    else:
        avg_estimated_demand = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50.0, "max": 300.0, "type": "float"}
    
    # Calculate safety stock based on coverage and variability
    safety_stock = safety_multiplier * avg_estimated_demand * coverage_periods
    
    # Calculate target inventory level
    target_inventory = base_stock + safety_stock
    
    # Apply emergency boost if effective inventory is critically low
    if effective_inventory < emergency_threshold:
        target_inventory *= emergency_boost
    
    # Calculate order amount with smoothing
    raw_order = max(0, target_inventory - effective_inventory)
    
    # Order smoothing factor - prevents large order swings
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    
    # Apply smoothing: blend with previous order if available
    # Since we can't store state, we estimate previous order from pipeline
    if len(pipeline_orders) > 0:
        previous_order = pipeline_orders[-1]  # Most recent order placed
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * previous_order
    else:
        smoothed_order = raw_order
    
    # Round to nearest integer (realistic ordering)
    order_amount = int(round(max(0, smoothed_order)))
    
    return order_amount
