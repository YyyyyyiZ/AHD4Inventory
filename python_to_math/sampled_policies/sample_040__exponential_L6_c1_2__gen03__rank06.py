# sample_id: 040
# folder: deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2plural_8_r6
# distribution: exponential_L6_c1_2
# generation: 3
# rank_in_population_file: 6
# objective: 6145.5
# test_objective: 6290.117
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;order_up_to;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 353.1678105626499  # OPT_PARAM: {"initial": 353.1678105626499, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 46.207982248122036  # OPT_PARAM: {"initial": 46.207982248122036, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 50.59999999999991  # OPT_PARAM: {"initial": 50.59999999999991, "min": 10, "max": 500, "type": "float"}
    smoothing_factor = 0.06586766248144076  # OPT_PARAM: {"initial": 0.06586766248144076, "min": 0.01, "max": 1.0, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.0, "max": 1.0, "type": "float"}
    adjustment_factor = 0.9224417153025465  # OPT_PARAM: {"initial": 0.9224417153025465, "min": 0.0, "max": 1.0, "type": "float"}
    demand_adjustment = 0.3000000000004861  # OPT_PARAM: {"initial": 0.3000000000004861, "min": 0.0, "max": 0.5, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate weighted pipeline (emphasize near-term arrivals)
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_weight ** i
        weighted_pipeline += order * weight
    
    # Adjust base stock based on recent demand pattern
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    if recent_arrivals > 0:
        demand_ratio = min(2.0, recent_arrivals / max(1.0, demand_forecast))
        adjusted_base = base_stock * (1.0 + demand_adjustment * (demand_ratio - 1.0))
    else:
        adjusted_base = base_stock
    
    # Apply pipeline composition adjustment
    adjusted_base = adjusted_base * adjustment_factor
    
    # Add safety stock buffer
    target_inventory = adjusted_base + safety_stock
    
    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)
    
    # Apply smoothing using recent pipeline orders
    if len(pipeline_orders) > 0:
        recent_avg = sum(pipeline_orders[-min(3, len(pipeline_orders)):]) / min(3, len(pipeline_orders))
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * recent_avg
    else:
        smoothed_order = raw_order
    
    # Round to nearest integer
    order_amount = int(round(smoothed_order))
    
    return order_amount
