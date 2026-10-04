# policy_hash: 0a5c14bdb46ccda6db6ab3c51cb3f0d956249211cdef490f70dd97ae0fe0cf5d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 1244.64
# best_prompt_performance: 1243.34
# best_rel_error_pct: 0.104448
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_232131.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 286.12639721149395  # OPT_PARAM: {"initial": 286.12639721149395, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 28.167957707612455  # OPT_PARAM: {"initial": 28.167957707612455, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand based on recent pipeline arrivals
    # (pipeline_orders[0] arrived today, pipeline_orders[1] arrives tomorrow)
    if len(pipeline_orders) >= 2 and pipeline_orders[0] > 0:
        # Use recent arrivals as demand indicator
        recent_demand_estimate = pipeline_orders[0] * demand_forecast_factor
    else:
        recent_demand_estimate = 100.0  # Default estimate

    # Adjust base stock based on recent demand pattern
    adjusted_base_stock = base_stock + safety_stock
    if recent_demand_estimate > 110:
        adjusted_base_stock += 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 100, "type": "float"}
    elif recent_demand_estimate < 90:
        adjusted_base_stock -= 15.0  # OPT_PARAM: {"initial": 15.0, "min": 0, "max": 100, "type": "float"}

    # Calculate order amount with smoothing
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.3492506611990131  # OPT_PARAM: {"initial": 0.3492506611990131, "min": 0.1, "max": 1.0, "type": "float"}
    if raw_order > 200:
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = raw_order

    # Ensure integer order amount
    return order_amount
