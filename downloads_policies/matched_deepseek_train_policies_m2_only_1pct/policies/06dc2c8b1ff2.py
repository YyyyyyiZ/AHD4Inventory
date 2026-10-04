# policy_hash: 06dc2c8b1ff2520058bc2f3ff9b6698bf437c27b640c0d4682e00668b767c432
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 6228.88
# best_prompt_performance: 6228.88
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_094227.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 550.0  # OPT_PARAM: {"initial": 550.0, "min": 300, "max": 900, "type": "float"}
    demand_forecast = 81.03310541965274  # OPT_PARAM: {"initial": 81.03310541965274, "min": 60, "max": 150, "type": "float"}
    lead_time = 6

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * lead_time

    # Dynamic safety stock based on pipeline variability
    safety_factor = 1.118868336114468  # OPT_PARAM: {"initial": 1.118868336114468, "min": 0.8, "max": 2.5, "type": "float"}

    # Estimate demand variability from pipeline orders
    if len(pipeline_orders) > 1:
        pipeline_mean = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_variance = sum((q - pipeline_mean) ** 2 for q in pipeline_orders) / len(pipeline_orders)
        variability_factor = max(0.5, min(2.0, 1.0 + pipeline_variance / 10000))
    else:
        variability_factor = 1.0

    safety_stock = safety_factor * demand_forecast * variability_factor

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Apply base stock policy
    order_amount = max(0, target_inventory - inventory_position)

    # Adaptive smoothing based on inventory position
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 1.0, "type": "float"}

    # Reduce smoothing when inventory is very low
    if inventory_position < demand_forecast * 2:
        effective_smoothing = min(1.0, smoothing_factor * 1.5)
    else:
        effective_smoothing = smoothing_factor

    if order_amount > 0:
        order_amount = effective_smoothing * order_amount

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
