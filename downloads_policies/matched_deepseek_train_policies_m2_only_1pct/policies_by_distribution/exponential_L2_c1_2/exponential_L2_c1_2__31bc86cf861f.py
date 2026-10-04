# policy_hash: 31bc86cf861f4bcd581874a9a931ba005580691dc174143dc5fc8e69a56570bf
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 37
# source_prompt_files: 1
# best_target_performance: 5918.58
# best_prompt_performance: 5918.5
# best_rel_error_pct: 0.001352
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_224630.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 182.837304862073  # OPT_PARAM: {"initial": 182.837304862073, "min": 150, "max": 250, "type": "float"}
    safety_stock = 42.894581387959256  # OPT_PARAM: {"initial": 42.894581387959256, "min": 30, "max": 80, "type": "float"}
    pipeline_weight = 0.9235620896564536  # OPT_PARAM: {"initial": 0.9235620896564536, "min": 0.8, "max": 1.0, "type": "float"}
    demand_buffer = 1.186367946982734  # OPT_PARAM: {"initial": 1.186367946982734, "min": 1.0, "max": 1.5, "type": "float"}
    next_arrival_weight = 0.21365922481126762  # OPT_PARAM: {"initial": 0.21365922481126762, "min": 0.0, "max": 0.5, "type": "float"}
    max_order_fraction = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.8, "type": "float"}

    # Calculate effective inventory position with full pipeline consideration
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock considering upcoming arrivals more conservatively
    next_arrival = pipeline_orders[0] if pipeline_orders else 0
    adjusted_base = base_stock * demand_buffer - next_arrival * next_arrival_weight

    # Calculate target with safety stock
    target = adjusted_base + safety_stock

    # Calculate order amount
    order_amount = max(0, target - inventory_position)

    # Apply smoother order cap
    if order_amount > 0:
        order_amount = min(order_amount, base_stock * max_order_fraction)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
