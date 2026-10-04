# sample_id: 085
# folder: deepseek-chat_normal_std30_L4_c1_2_50_plain_processed_scipy_15_default_e1-e2-m2_4_r1
# distribution: normal_std30_L4_c1_2
# generation: 9
# rank_in_population_file: 2
# objective: 2148.37423
# test_objective: 2214.44297
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 421.6446046499665  # OPT_PARAM: {"initial": 421.6446046499665, "min": 300, "max": 600, "type": "float"}
    safety_stock = 10.112929000695772  # OPT_PARAM: {"initial": 10.112929000695772, "min": 10, "max": 50, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    demand_forecast_factor = 0.5157159963654885  # OPT_PARAM: {"initial": 0.5157159963654885, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.23388874095375883  # OPT_PARAM: {"initial": 0.23388874095375883, "min": 0.1, "max": 0.5, "type": "float"}
    min_order = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 10, "max": 40, "type": "float"}
    max_order = 88.51464456153231  # OPT_PARAM: {"initial": 88.51464456153231, "min": 80, "max": 200, "type": "float"}
    
    # Calculate average pipeline demand (excluding zeros in planning phase)
    non_zero_pipeline = [q for q in pipeline_orders if q > 0]
    if non_zero_pipeline:
        avg_pipeline = sum(non_zero_pipeline) / len(non_zero_pipeline)
    else:
        avg_pipeline = 100.0  # default estimate
    
    # Forecast demand based on pipeline average
    forecast_demand = avg_pipeline * demand_forecast_factor
    
    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline
    
    # Target inventory level
    target_inventory = base_stock + safety_stock + forecast_demand
    
    # Calculate order with smoothing
    order_needed = target_inventory - inventory_position
    smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * avg_pipeline
    
    # Apply bounds
    order_amount = max(min_order, min(max_order, smoothed_order))
    
    return order_amount
