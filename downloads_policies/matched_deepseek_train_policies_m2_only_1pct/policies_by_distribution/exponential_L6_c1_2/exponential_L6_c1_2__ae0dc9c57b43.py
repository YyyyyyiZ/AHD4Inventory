# policy_hash: ae0dc9c57b435b724eccf10f0493d810b26bd8571928104cfa114d6ec4309835
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 6188.92
# best_prompt_performance: 6188.92
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_094643.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 552.8000000000827  # OPT_PARAM: {"initial": 552.8000000000827, "min": 300, "max": 900, "type": "float"}
    demand_forecast = 85.0  # OPT_PARAM: {"initial": 85.0, "min": 60, "max": 150, "type": "float"}
    lead_time = 6

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * lead_time

    # Dynamic safety stock with improved variability factor
    safety_factor = 1.15  # OPT_PARAM: {"initial": 1.15, "min": 0.8, "max": 2.5, "type": "float"}

    # Better variability estimation using recent pipeline orders
    if len(pipeline_orders) > 1:
        recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
        recent_mean = sum(recent_orders) / len(recent_orders)
        recent_variance = sum((q - recent_mean) ** 2 for q in recent_orders) / len(recent_orders)
        variability_factor = max(0.7, min(1.5, 1.0 + recent_variance / 4000))
    else:
        variability_factor = 1.0

    safety_stock = safety_factor * demand_forecast * variability_factor

    # Calculate target inventory level with base stock adjustment
    target_inventory = expected_lead_time_demand + safety_stock
    target_inventory = min(target_inventory, base_stock)

    # Apply base stock policy
    order_amount = max(0, target_inventory - inventory_position)

    # Adaptive smoothing based on inventory position
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 1.0, "type": "float"}

    # More aggressive smoothing when inventory is high
    if inventory_position > demand_forecast * 3:
        effective_smoothing = max(0.2, smoothing_factor * 0.8)
    elif inventory_position < demand_forecast * 1.2:
        effective_smoothing = min(1.0, smoothing_factor * 1.3)
    else:
        effective_smoothing = smoothing_factor

    if order_amount > 0:
        order_amount = effective_smoothing * order_amount

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
