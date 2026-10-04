# policy_hash: 0905aa2737709796ef5f65e681f30a8701eabeae35f63c5710836ec79c5e364b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 1171.4
# best_prompt_performance: 1171.4
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_231722.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 284.76682878416784  # OPT_PARAM: {"initial": 284.76682878416784, "min": 200, "max": 400, "type": "float"}
    safety_stock = 24.76682878416778  # OPT_PARAM: {"initial": 24.76682878416778, "min": 10, "max": 80, "type": "float"}
    demand_forecast_factor = 0.9923332917334156  # OPT_PARAM: {"initial": 0.9923332917334156, "min": 0.7, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted average of recent arrivals
    if len(pipeline_orders) >= 2 and pipeline_orders[0] > 0:
        # Use weighted average of last two arrivals
        weight_recent = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 0.9, "type": "float"}
        recent_demand_estimate = (weight_recent * pipeline_orders[0] +
                                 (1 - weight_recent) * pipeline_orders[1])
    else:
        recent_demand_estimate = 100.0

    # Apply demand forecast factor
    forecasted_demand = recent_demand_estimate * demand_forecast_factor

    # Dynamic base stock adjustment based on forecasted demand
    adjusted_base_stock = base_stock + safety_stock

    # More responsive demand-based adjustment
    if forecasted_demand > 115:
        adjusted_base_stock += 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 40, "type": "float"}
    elif forecasted_demand > 105:
        adjusted_base_stock += 5.0  # OPT_PARAM: {"initial": 5.0, "min": 0, "max": 20, "type": "float"}
    elif forecasted_demand < 85:
        adjusted_base_stock -= 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 30, "type": "float"}
    elif forecasted_demand < 95:
        adjusted_base_stock -= 5.0  # OPT_PARAM: {"initial": 5.0, "min": 0, "max": 15, "type": "float"}

    # Calculate order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Progressive smoothing with more aggressive reduction for large orders
    if raw_order > 250:
        smoothing_factor = 0.4670475952762375  # OPT_PARAM: {"initial": 0.4670475952762375, "min": 0.1, "max": 0.4, "type": "float"}
        order_amount = raw_order * smoothing_factor
    elif raw_order > 150:
        smoothing_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.2, "max": 0.6, "type": "float"}
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = raw_order

    # Round to nearest integer
    return order_amount
