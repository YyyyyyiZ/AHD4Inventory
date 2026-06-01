# sample_id: 053
# folder: deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_10_r3
# distribution: poisson_L6_c1_5
# generation: 4
# rank_in_population_file: 10
# objective: 1759.60213
# test_objective: 1580.4407
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;order_up_to;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 534.6011611483775  # OPT_PARAM: {"initial": 534.6011611483775, "min": 400, "max": 700, "type": "float"}
    safety_stock = 44.65053849986418  # OPT_PARAM: {"initial": 44.65053849986418, "min": 20, "max": 80, "type": "float"}
    demand_forecast = 102.24532485660083  # OPT_PARAM: {"initial": 102.24532485660083, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.1, "type": "float"}
    order_smoothing_min = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 0.9, "type": "float"}
    order_smoothing_max = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 1.1, "max": 1.5, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    
    # Calculate effective inventory position with full pipeline weight
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline
    
    # Adjust base stock based on lost sales cost ratio
    adjusted_base_stock = base_stock * lost_sales_weight
    
    # Calculate order-up-to level
    order_up_to = adjusted_base_stock + safety_stock
    
    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)
    
    # Apply smoother ordering bounds based on forecast
    if raw_order > 0:
        min_order = demand_forecast * order_smoothing_min
        max_order = demand_forecast * order_smoothing_max
        order_amount = max(min_order, min(raw_order, max_order))
    else:
        order_amount = 0
    
    return order_amount
