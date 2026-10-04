# policy_hash: 5e6d40328300c995424d632750fcd641f5c9a3ca245728f304cd58e9bb5e3f7b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 1135.97
# best_prompt_performance: 1135.97
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_232804.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 329.4178789107286  # OPT_PARAM: {"initial": 329.4178789107286, "min": 200, "max": 350, "type": "float"}
    safety_stock = 45.47169374710231  # OPT_PARAM: {"initial": 45.47169374710231, "min": 5, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using simple average of recent arrivals
    if len(pipeline_orders) >= 2 and pipeline_orders[0] > 0:
        # Use average of last two arrivals
        recent_demand_estimate = (pipeline_orders[0] + pipeline_orders[1]) / 2
    else:
        recent_demand_estimate = 100.0

    # Dynamic base stock adjustment
    adjusted_base_stock = base_stock + safety_stock

    # More aggressive demand-based adjustment
    if recent_demand_estimate > 110:
        adjusted_base_stock += 25.0  # OPT_PARAM: {"initial": 25.0, "min": 10, "max": 50, "type": "float"}
    elif recent_demand_estimate > 100:
        adjusted_base_stock += 10.0  # OPT_PARAM: {"initial": 10.0, "min": 5, "max": 25, "type": "float"}
    elif recent_demand_estimate < 90:
        adjusted_base_stock -= 20.0  # OPT_PARAM: {"initial": 20.0, "min": 10, "max": 40, "type": "float"}
    elif recent_demand_estimate < 95:
        adjusted_base_stock -= 8.0  # OPT_PARAM: {"initial": 8.0, "min": 3, "max": 20, "type": "float"}

    # Calculate order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Progressive smoothing
    if raw_order > 200:
        smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.5, "type": "float"}
        order_amount = raw_order * smoothing_factor
    elif raw_order > 100:
        smoothing_factor = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.3, "max": 0.8, "type": "float"}
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = raw_order

    # Round to nearest integer
    return order_amount
