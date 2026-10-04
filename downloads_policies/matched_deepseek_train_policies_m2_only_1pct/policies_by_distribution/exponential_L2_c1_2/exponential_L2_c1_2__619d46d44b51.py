# policy_hash: 619d46d44b51e2c91a5b6d41e9c0f0b4b42c98acb681c746b89828787b6c0543
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 6431.03
# best_prompt_performance: 6431.03
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223102.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 207.94635405797283  # OPT_PARAM: {"initial": 207.94635405797283, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_buffer = 30.0  # OPT_PARAM: {"initial": 30.0, "min": 0, "max": 100, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using recent pipeline arrivals
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    next_arrival = pipeline_orders[1] if len(pipeline_orders) > 1 else 0

    # Adjust base stock based on recent demand patterns
    adjusted_base = base_stock
    if recent_arrivals > 150:  # High recent demand indicator
        adjusted_base += demand_buffer
    elif recent_arrivals < 50 and next_arrival < 50:  # Low recent demand
        adjusted_base = max(base_stock * 0.8, safety_stock)

    # Calculate order amount with safety stock consideration
    target_inventory = max(adjusted_base, safety_stock + sum(pipeline_orders))
    order_amount = max(0, target_inventory - inventory_position)

    # Smooth ordering to avoid extreme fluctuations
    if order_amount > 300:  # OPT_PARAM: {"initial": 300, "min": 100, "max": 500, "type": "float"}
        order_amount = 300 + (order_amount - 300) * 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 0.9, "type": "float"}

    return order_amount
