# policy_hash: 6dd0ea8501a5426f9d05730da3f561d8bd056d1d09b64c5ae715675fc455366b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 1128.8
# best_prompt_performance: 1128.8
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_232448.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 305.6943150492216  # OPT_PARAM: {"initial": 305.6943150492216, "min": 200, "max": 400, "type": "float"}
    safety_stock = 44.92246045111829  # OPT_PARAM: {"initial": 44.92246045111829, "min": 10, "max": 80, "type": "float"}
    demand_forecast_factor = 1.05  # OPT_PARAM: {"initial": 1.05, "min": 0.7, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted average of recent arrivals
    if len(pipeline_orders) >= 2 and pipeline_orders[0] > 0:
        # Use recent demand pattern for better forecasting
        recent_demand_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 0.9, "type": "float"}
        if len(pipeline_orders) >= 3:
            # Weight recent arrivals more heavily
            recent_arrivals = [pipeline_orders[0], pipeline_orders[1]]
            recent_demand_estimate = sum(recent_arrivals) / len(recent_arrivals) * demand_forecast_factor
        else:
            recent_demand_estimate = 100.0
    else:
        recent_demand_estimate = 100.0

    # Dynamic base stock adjustment based on demand estimate
    adjusted_base_stock = base_stock + safety_stock

    # More responsive demand-based adjustment
    if recent_demand_estimate > 115:
        adjusted_base_stock += 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 40, "type": "float"}
    elif recent_demand_estimate > 105:
        adjusted_base_stock += 5.0  # OPT_PARAM: {"initial": 5.0, "min": 0, "max": 20, "type": "float"}
    elif recent_demand_estimate < 85:
        adjusted_base_stock -= 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 30, "type": "float"}
    elif recent_demand_estimate < 95:
        adjusted_base_stock -= 5.0  # OPT_PARAM: {"initial": 5.0, "min": 0, "max": 15, "type": "float"}

    # Calculate raw order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Smoother order adjustment to reduce volatility
    if raw_order > 200:
        smoothing_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.2, "max": 0.7, "type": "float"}
        order_amount = raw_order * smoothing_factor
    elif raw_order > 100:
        smoothing_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.4, "max": 0.9, "type": "float"}
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = raw_order

    # Round to nearest integer
    return order_amount
