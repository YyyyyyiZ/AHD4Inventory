# policy_hash: c6f12b14cbd018e0835c9d0c84deaeac10eb3144c311939aaf8d4b8fde8a50b5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 1225.82
# best_prompt_performance: 1225.82
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_084619.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 446.0847360478336  # OPT_PARAM: {"initial": 446.0847360478336, "min": 400, "max": 650, "type": "float"}
    demand_forecast = 95.30177593858265  # OPT_PARAM: {"initial": 95.30177593858265, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.024963455883442436  # OPT_PARAM: {"initial": 0.024963455883442436, "min": 0.01, "max": 0.5, "type": "float"}
    safety_stock_multiplier = 1.3740723481157129  # OPT_PARAM: {"initial": 1.3740723481157129, "min": 0.8, "max": 3.0, "type": "float"}
    pipeline_coverage = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 2.0, "max": 5.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate pipeline-adjusted demand forecast
    pipeline_weeks = len(pipeline_orders)
    pipeline_adjustment = max(0, pipeline_coverage - pipeline_weeks)
    adjusted_forecast = demand_forecast * (1 + 0.05 * pipeline_adjustment)

    # Dynamic safety stock
    safety_stock = safety_stock_multiplier * adjusted_forecast

    # Adjusted base stock level with safety stock
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order-up-to level
    order_up_to = max(adjusted_base_stock, inventory_position + adjusted_forecast)

    # Calculate required order
    required_order = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid large order swings
    smoothed_order = smoothing_factor * required_order + (1 - smoothing_factor) * adjusted_forecast

    # Round to nearest integer and ensure non-negative
    order_amount = max(0, round(smoothed_order))

    return order_amount
