# policy_hash: 1eac87225ea6f7b5e5edeee3e04ac50734649f5bc5a88eec35d8830570f19e9d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 1419.18
# best_prompt_performance: 1419.18
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_231248.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 282.75860635708136  # OPT_PARAM: {"initial": 282.75860635708136, "min": 200, "max": 400, "type": "float"}
    safety_stock = 42.10255801215263  # OPT_PARAM: {"initial": 42.10255801215263, "min": 20, "max": 80, "type": "float"}
    demand_forecast_factor = 1.05  # OPT_PARAM: {"initial": 1.05, "min": 0.8, "max": 1.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using recent arrivals with adjustment
    if len(pipeline_orders) >= 2 and pipeline_orders[0] > 0:
        recent_demand_estimate = pipeline_orders[0] * demand_forecast_factor
    else:
        recent_demand_estimate = 100.0

    # Dynamic base stock adjustment based on demand estimate
    adjusted_base_stock = base_stock + safety_stock
    if recent_demand_estimate > 115:
        adjusted_base_stock += 25.0  # OPT_PARAM: {"initial": 25.0, "min": 10, "max": 50, "type": "float"}
    elif recent_demand_estimate < 85:
        adjusted_base_stock -= 10.0  # OPT_PARAM: {"initial": 10.0, "min": 5, "max": 30, "type": "float"}

    # Calculate order with proportional adjustment
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Smooth large orders more aggressively
    smoothing_factor = 0.379987205178253  # OPT_PARAM: {"initial": 0.379987205178253, "min": 0.1, "max": 0.5, "type": "float"}
    if raw_order > 150:
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = raw_order

    # Round to nearest integer
    return order_amount
