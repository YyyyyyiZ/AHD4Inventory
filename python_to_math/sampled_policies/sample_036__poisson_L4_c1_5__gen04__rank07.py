# sample_id: 036
# folder: deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r7
# distribution: poisson_L4_c1_5
# generation: 4
# rank_in_population_file: 7
# objective: 1504.18025
# test_objective: 1526.05274
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 460.6106521270296  # OPT_PARAM: {"initial": 460.6106521270296, "min": 400, "max": 550, "type": "float"}
    safety_stock = 51.02889525595642  # OPT_PARAM: {"initial": 51.02889525595642, "min": 40, "max": 100, "type": "float"}
    demand_forecast = 94.63494303930437  # OPT_PARAM: {"initial": 94.63494303930437, "min": 90, "max": 110, "type": "float"}
    alpha = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 0.95, "type": "float"}
    beta = 0.25  # OPT_PARAM: {"initial": 0.25, "min": 0.15, "max": 0.5, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_forecast * lead_time
    
    # Target inventory position: base stock adjusted for lead time demand
    target_inventory = base_stock + safety_stock
    
    # Calculate order needed to reach target
    order_needed = target_inventory - inventory_position
    
    if order_needed > 0:
        # Order smoothing: mix of needed amount and forecasted demand
        order_amount = alpha * order_needed + (1 - alpha) * demand_forecast
        # Additional smoothing to prevent over-ordering
        order_amount = beta * order_amount + (1 - beta) * demand_forecast
    else:
        order_amount = 0
    
    # Ensure non-negative integer order
    return order_amount
