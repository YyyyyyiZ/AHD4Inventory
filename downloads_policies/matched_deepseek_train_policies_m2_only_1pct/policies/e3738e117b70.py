# policy_hash: e3738e117b701c7e8596e03052eca8ac9be20e218a46eea14d3a769324f088a2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 5995.2
# best_prompt_performance: 5995.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223358.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 225.3099489593911  # OPT_PARAM: {"initial": 225.3099489593911, "min": 50, "max": 400, "type": "float"}
    safety_stock = 48.76219718977453  # OPT_PARAM: {"initial": 48.76219718977453, "min": 20, "max": 150, "type": "float"}
    demand_buffer = 1.0212128557701485  # OPT_PARAM: {"initial": 1.0212128557701485, "min": 0.8, "max": 2.0, "type": "float"}
    smoothing_factor = 0.41761765980564447  # OPT_PARAM: {"initial": 0.41761765980564447, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent pipeline orders
    # Pipeline orders reflect past demand, so we use them as demand proxy
    if len(pipeline_orders) >= 2:
        # More weight on recent orders
        recent_demand_estimate = (pipeline_orders[-1] * 0.7 + pipeline_orders[-2] * 0.3) * demand_buffer
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
        # Smooth large orders more aggressively
        if raw_order > 0.5 * dynamic_target:
            order_amount = raw_order * smoothing_factor
        else:
            order_amount = raw_order
    else:
        order_amount = 0

    return order_amount
