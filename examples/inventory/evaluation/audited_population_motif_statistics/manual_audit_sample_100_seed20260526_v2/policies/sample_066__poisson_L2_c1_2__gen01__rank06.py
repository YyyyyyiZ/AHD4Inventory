# sample_id: 066
# folder: deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_10_r2
# distribution: poisson_L2_c1_2
# generation: 1
# rank_in_population_file: 6
# objective: 1183.82
# test_objective: 1181.211
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding;nonlinear_gap_transform
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 294.00072750770767  # OPT_PARAM: {"initial": 294.00072750770767, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 100, "type": "float"}
    demand_forecast_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 1.5, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Adjust base stock based on pipeline variability
    pipeline_variance = sum((q - sum(pipeline_orders)/len(pipeline_orders))**2 for q in pipeline_orders) if len(pipeline_orders) > 0 else 0
    pipeline_adjustment = min(50, max(-50, pipeline_variance * 0.1))  # OPT_PARAM: {"initial": 0.1, "min": 0, "max": 1, "type": "float"}
    
    # Dynamic target based on inventory position and safety stock
    dynamic_target = base_stock + safety_stock + pipeline_adjustment
    
    # Calculate order amount with smoothing
    raw_order = max(0, dynamic_target - inventory_position)
    
    # Apply demand forecast adjustment
    recent_demand_estimate = sum(pipeline_orders) / max(1, len(pipeline_orders)) * demand_forecast_factor
    adjusted_order = max(0, raw_order * 0.7 + recent_demand_estimate * 0.3)  # OPT_PARAM: {"initial": 0.7, "min": 0.1, "max": 1.0, "type": "float"}
    
    # Round to nearest integer (as required by output type)
    order_amount = int(round(adjusted_order))
    
    return order_amount
