# sample_id: 028
# folder: deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_10_r1
# distribution: exponential_L4_c1_2
# generation: 6
# rank_in_population_file: 6
# objective: 6118.04
# test_objective: 6175.142
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;order_up_to;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 192.40570617005534  # OPT_PARAM: {"initial": 192.40570617005534, "min": 100, "max": 300, "type": "float"}
    safety_stock = 42.40570617005488  # OPT_PARAM: {"initial": 42.40570617005488, "min": 10, "max": 80, "type": "float"}
    demand_forecast_factor = 1.3013911932804665  # OPT_PARAM: {"initial": 1.3013911932804665, "min": 0.8, "max": 1.5, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Use more recent pipeline orders for demand estimation (last 3 periods)
    recent_arrivals = pipeline_orders[:3]
    if any(recent_arrivals):
        # Weight recent arrivals more heavily
        weights = [0.5, 0.3, 0.2]  # Decreasing weights for older orders
        weighted_sum = sum(w * val for w, val in zip(weights, recent_arrivals))
        avg_recent = weighted_sum / sum(weights[:len(recent_arrivals)])
        recent_demand_estimate = avg_recent * demand_forecast_factor
    else:
        recent_demand_estimate = 0
    
    # Adjust base stock based on recent demand and safety stock
    adjusted_base_stock = base_stock + safety_stock + recent_demand_estimate
    
    # Calculate order amount using inventory position
    order_amount = max(0, adjusted_base_stock - inventory_position)
    
    # Apply smoothing with pipeline-aware adjustment
    if len(pipeline_orders) > 0:
        # Weighted average of pipeline orders
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        # Blend order amount with pipeline average
        smoothed_order = (smoothing_factor * order_amount + 
                         (1 - smoothing_factor) * avg_pipeline * pipeline_weight)
        order_amount = max(0, smoothed_order)
    
    # Round to nearest integer
    order_amount = int(round(order_amount))
    
    return order_amount
