# policy_hash: 0f6ff6c98b1a341e9c783ff0b1ae97d5805dcf7a8451841644152e1e71b2aad3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 21
# source_prompt_files: 1
# best_target_performance: 5930.83
# best_prompt_performance: 5930.83
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_224320.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 273.1435647616412  # OPT_PARAM: {"initial": 273.1435647616412, "min": 100, "max": 300, "type": "float"}
    safety_stock = 52.333909822406014  # OPT_PARAM: {"initial": 52.333909822406014, "min": 30, "max": 120, "type": "float"}
    demand_buffer = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.9, "max": 1.5, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    pipeline_weight_recent = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent pipeline orders
    # Pipeline orders reflect past demand, so we use them as demand proxy
    if len(pipeline_orders) >= 2:
        # More weight on recent orders
        recent_demand_estimate = (pipeline_orders[-1] * pipeline_weight_recent +
                                 pipeline_orders[-2] * (1 - pipeline_weight_recent)) * demand_buffer
    elif len(pipeline_orders) == 1:
        recent_demand_estimate = pipeline_orders[-1] * demand_buffer
    else:
        recent_demand_estimate = 0

    # Dynamic target: base stock adjusted for recent demand patterns
    dynamic_target = max(base_stock, safety_stock + recent_demand_estimate)

    # Calculate raw order needed
    raw_order = max(0, dynamic_target - inventory_position)

    # Apply exponential smoothing to reduce order volatility
    # This helps avoid overreacting to temporary inventory fluctuations
    if raw_order > 0:
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = 0

    return order_amount
