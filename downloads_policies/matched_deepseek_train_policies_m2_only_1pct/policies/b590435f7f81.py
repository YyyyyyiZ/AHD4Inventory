# policy_hash: b590435f7f81a69227a28cbdc8598af2ccda6ded4057960f00a307db1b3bd3ae
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 1150.55
# best_prompt_performance: 1150.55
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_231834.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 277.58932258366866  # OPT_PARAM: {"initial": 277.58932258366866, "min": 200, "max": 400, "type": "float"}
    safety_stock = 32.58932258366813  # OPT_PARAM: {"initial": 32.58932258366813, "min": 10, "max": 80, "type": "float"}
    demand_forecast_factor = 0.95  # OPT_PARAM: {"initial": 0.95, "min": 0.7, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using recent arrivals with smoothing
    if len(pipeline_orders) >= 2 and pipeline_orders[0] > 0:
        # Weighted average of recent arrivals
        recent_demand_estimate = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.3, "max": 0.8, "type": "float"}
    else:
        recent_demand_estimate = 100.0

    # Dynamic base stock adjustment
    adjusted_base_stock = base_stock + safety_stock

    # More granular demand-based adjustment
    if recent_demand_estimate > 115:
        adjusted_base_stock += 25.0  # OPT_PARAM: {"initial": 25.0, "min": 10, "max": 50, "type": "float"}
    elif recent_demand_estimate > 105:
        adjusted_base_stock += 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 30, "type": "float"}
    elif recent_demand_estimate < 85:
        adjusted_base_stock -= 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 40, "type": "float"}
    elif recent_demand_estimate < 95:
        adjusted_base_stock -= 8.0  # OPT_PARAM: {"initial": 8.0, "min": 0, "max": 20, "type": "float"}

    # Calculate order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Progressive smoothing based on order size
    if raw_order > 250:
        smoothing_factor = 0.3177437641434845  # OPT_PARAM: {"initial": 0.3177437641434845, "min": 0.1, "max": 0.5, "type": "float"}
        order_amount = raw_order * smoothing_factor
    elif raw_order > 150:
        smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.3, "max": 0.8, "type": "float"}
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = raw_order

    # Round to nearest integer
    return order_amount
