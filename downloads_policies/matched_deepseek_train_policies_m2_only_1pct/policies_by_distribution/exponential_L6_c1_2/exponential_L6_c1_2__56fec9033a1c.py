# policy_hash: 56fec9033a1cf8723b3819284eed8d1df126f5d179826f5eda6b2c164e6d5bdd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 6131.76
# best_prompt_performance: 6131.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_094849.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 771.1999999999921  # OPT_PARAM: {"initial": 771.1999999999921, "min": 400, "max": 1000, "type": "float"}
    demand_forecast = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 70, "max": 130, "type": "float"}
    lead_time = 6

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * lead_time

    # Safety stock with higher factor for lost sales penalty
    safety_factor = 1.8  # OPT_PARAM: {"initial": 1.8, "min": 1.2, "max": 3.0, "type": "float"}

    # Simple variability factor based on pipeline orders
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        variability_factor = 1.0 + min(0.5, abs(avg_pipeline - demand_forecast) / (demand_forecast + 1))
    else:
        variability_factor = 1.0

    safety_stock = safety_factor * demand_forecast * variability_factor

    # Target inventory level
    target_inventory = expected_lead_time_demand + safety_stock
    target_inventory = min(target_inventory, base_stock)

    # Base stock policy
    order_amount = max(0, target_inventory - inventory_position)

    # Order smoothing with simpler logic
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}

    # Apply smoothing only for large orders
    if order_amount > demand_forecast * 2:
        order_amount = smoothing_factor * order_amount

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
