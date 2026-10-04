# policy_hash: 7431976cbf51b78494e7f883f4e92618f7c7adb913f04b78983bf9a88705320b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 1226.04
# best_prompt_performance: 1226.04
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_233715.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 285.0  # OPT_PARAM: {"initial": 285.0, "min": 200, "max": 400, "type": "float"}
    safety_stock = 25.0  # OPT_PARAM: {"initial": 25.0, "min": 10, "max": 80, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand estimation using recent arrivals
    if len(pipeline_orders) >= 2:
        recent_demand_estimate = (pipeline_orders[0] + pipeline_orders[1]) / 2
    else:
        recent_demand_estimate = 100.0

    # Dynamic base stock adjustment
    adjusted_base_stock = base_stock + safety_stock

    # More responsive demand-based adjustment
    if recent_demand_estimate > 115:
        adjusted_base_stock += 20.0  # OPT_PARAM: {"initial": 20.0, "min": 5, "max": 40, "type": "float"}
    elif recent_demand_estimate > 105:
        adjusted_base_stock += 8.0  # OPT_PARAM: {"initial": 8.0, "min": 0, "max": 20, "type": "float"}
    elif recent_demand_estimate < 85:
        adjusted_base_stock -= 20.0  # OPT_PARAM: {"initial": 20.0, "min": 5, "max": 30, "type": "float"}
    elif recent_demand_estimate < 95:
        adjusted_base_stock -= 8.0  # OPT_PARAM: {"initial": 8.0, "min": 0, "max": 15, "type": "float"}

    # Calculate order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Progressive smoothing
    if raw_order > 250:
        smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.3, "max": 0.7, "type": "float"}
        order_amount = raw_order * smoothing_factor
    elif raw_order > 150:
        smoothing_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.5, "max": 0.9, "type": "float"}
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = raw_order

    # Round to nearest integer
    return order_amount
