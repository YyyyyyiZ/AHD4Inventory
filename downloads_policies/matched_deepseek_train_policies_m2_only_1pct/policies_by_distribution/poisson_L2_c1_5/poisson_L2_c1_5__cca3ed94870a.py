# policy_hash: cca3ed94870abdbcb0a66c0e772913d36a14773d12c1d394f80a3fd2d6f7e9d4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1302.02
# best_prompt_performance: 1302.02
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_232511.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 285.190886636996  # OPT_PARAM: {"initial": 285.190886636996, "min": 200, "max": 350, "type": "float"}
    safety_stock = 40.19511158141674  # OPT_PARAM: {"initial": 40.19511158141674, "min": 15, "max": 60, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Better demand estimation using pipeline arrivals
    if len(pipeline_orders) >= 2:
        # Use weighted average with more weight on recent arrivals
        recent_demand_estimate = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.4, "max": 0.8, "type": "float"}
    else:
        recent_demand_estimate = 100.0

    # Dynamic base stock adjustment with smoother response
    adjusted_base_stock = base_stock + safety_stock

    # More gradual demand-based adjustments
    if recent_demand_estimate > 110:
        adjustment = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.5, "max": 2.0, "type": "float"}
        adjusted_base_stock += adjustment
    elif recent_demand_estimate < 90:
        adjustment = min(25.0, (90 - recent_demand_estimate) * 1.2)  # OPT_PARAM: {"initial": 1.2, "min": 0.5, "max": 2.0, "type": "float"}
        adjusted_base_stock -= adjustment

    # Calculate order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Progressive smoothing with continuous scaling
    if raw_order > 200:
        smoothing_factor = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.4, "max": 0.8, "type": "float"}
        order_amount = raw_order * smoothing_factor
    elif raw_order > 100:
        smoothing_factor = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.6, "max": 1.0, "type": "float"}
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = raw_order

    # Add small rounding buffer
    order_amount = int(order_amount + 0.5)

    # Ensure non-negative
    return order_amount
