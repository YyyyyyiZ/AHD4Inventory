# policy_hash: 0aca35de4ce5925b5ee77e618bc45b2306c3529d13af632cef6c3c4d340d50d4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 6236.94
# best_prompt_performance: 6236.92
# best_rel_error_pct: 0.000321
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_093807.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.0  # OPT_PARAM: {"initial": 450.0, "min": 100, "max": 800, "type": "float"}
    demand_forecast = 73.35571987752616  # OPT_PARAM: {"initial": 73.35571987752616, "min": 50, "max": 300, "type": "float"}
    lead_time = 6

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * lead_time

    # Calculate safety stock based on demand variability
    safety_factor = 0.8344973348486228  # OPT_PARAM: {"initial": 0.8344973348486228, "min": 0.5, "max": 3.0, "type": "float"}
    safety_stock = safety_factor * demand_forecast

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate order quantity
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
