# sample_id: 075
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r7
# distribution: poisson_L6_c1_2
# generation: 9
# rank_in_population_file: 9
# objective: 972.22
# test_objective: 951.996
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 530.8053146215685  # OPT_PARAM: {"initial": 530.8053146215685, "min": 450, "max": 600, "type": "float"}
    safety_stock = 52.00531462156949  # OPT_PARAM: {"initial": 52.00531462156949, "min": 20, "max": 80, "type": "float"}
    demand_forecast = 94.67244908223753  # OPT_PARAM: {"initial": 94.67244908223753, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    lost_sales_weight = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 1.0, "max": 1.5, "type": "float"}
    
    # Calculate effective pipeline (weighted average)
    weighted_pipeline = 0
    total_weight = 0
    for i, q in enumerate(pipeline_orders):
        weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
        weighted_pipeline += q * weight
        total_weight += weight
    
    if total_weight > 0:
        effective_pipeline = weighted_pipeline / total_weight * len(pipeline_orders)
    else:
        effective_pipeline = sum(pipeline_orders)
    
    # Calculate net inventory position
    net_inventory = on_hand_inventory + effective_pipeline
    
    # Adjust safety stock based on pipeline coverage
    pipeline_coverage = sum(pipeline_orders) / (demand_forecast * len(pipeline_orders)) if demand_forecast > 0 else 1.0
    adjusted_safety = safety_stock * (1.0 + 0.3 * (1.0 - min(1.0, pipeline_coverage)))
    
    # Calculate target with lost-sales bias
    target_inventory = base_stock + adjusted_safety * lost_sales_weight
    
    # Calculate order-up-to level
    order_up_to = max(0, target_inventory - net_inventory)
    
    # Apply smoothing
    smoothed_order = smoothing_factor * order_up_to + (1 - smoothing_factor) * demand_forecast
    
    # Round to nearest integer
    order_amount = max(0, int(round(smoothed_order)))
    
    return order_amount
