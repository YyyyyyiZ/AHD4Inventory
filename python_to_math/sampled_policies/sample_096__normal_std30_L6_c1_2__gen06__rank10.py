# sample_id: 096
# folder: deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2plural_4_r6
# distribution: normal_std30_L6_c1_2
# generation: 6
# rank_in_population_file: 10
# objective: 2308.9
# test_objective: 2277.102
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;order_up_to;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;threshold_order_activation;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 545.9771711201012  # OPT_PARAM: {"initial": 545.9771711201012, "min": 400, "max": 700, "type": "float"}
    safety_stock = 13.79731078150345  # OPT_PARAM: {"initial": 13.79731078150345, "min": 0, "max": 50, "type": "float"}
    demand_forecast_factor = 0.6003046695113123  # OPT_PARAM: {"initial": 0.6003046695113123, "min": 0.5, "max": 1.5, "type": "float"}
    smoothing_factor = 0.14594944369598148  # OPT_PARAM: {"initial": 0.14594944369598148, "min": 0.1, "max": 0.8, "type": "float"}
    min_order_qty = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 30, "type": "float"}
    max_order_qty = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 200, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand using simple average of recent pipeline orders
    if len(pipeline_orders) > 0:
        # Use last 3 pipeline orders as demand estimate
        recent_window = min(3, len(pipeline_orders))
        avg_recent_demand = sum(pipeline_orders[:recent_window]) / recent_window
    else:
        avg_recent_demand = 0
    
    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand
    
    # Calculate order amount with safety stock adjustment
    order_amount = max(0, adjusted_base_stock + safety_stock - inventory_position)
    
    # Apply smoothing to avoid extreme order fluctuations
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_pipeline
        order_amount = max(0, smoothed_order)
    
    # Apply ordering threshold to reduce small orders
    if order_amount < min_order_qty:
        order_amount = 0
    
    # Cap large orders to prevent overordering
    order_amount = min(order_amount, max_order_qty)
    
    # Round to nearest integer
    order_amount = int(round(order_amount))
    
    return order_amount
