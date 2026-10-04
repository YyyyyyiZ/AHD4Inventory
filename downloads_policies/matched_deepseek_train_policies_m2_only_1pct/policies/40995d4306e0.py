# policy_hash: 40995d4306e099451b2c4cb25fe69e9ccb6fd413c1d9811103607dec3d62beda
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 45
# source_prompt_files: 2
# best_target_performance: 1329.28
# best_prompt_performance: 1329.28
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031036.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 243.42950239857683  # OPT_PARAM: {"initial": 243.42950239857683, "min": 200, "max": 300, "type": "float"}
    safety_stock = 23.42950239857712  # OPT_PARAM: {"initial": 23.42950239857712, "min": 10, "max": 40, "type": "float"}
    demand_forecast_factor = 0.8016980338570983  # OPT_PARAM: {"initial": 0.8016980338570983, "min": 0.7, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast: average of last two pipeline orders
    if len(pipeline_orders) >= 2:
        expected_demand = ((pipeline_orders[-1] + pipeline_orders[-2]) / 2) * demand_forecast_factor
    elif pipeline_orders:
        expected_demand = pipeline_orders[-1] * demand_forecast_factor
    else:
        expected_demand = 100.0 * demand_forecast_factor

    # Dynamic base stock adjustment
    demand_adjustment = 0.4832929565205227  # OPT_PARAM: {"initial": 0.4832929565205227, "min": 0.4, "max": 0.8, "type": "float"}
    adjusted_base_stock = base_stock + safety_stock + (expected_demand * demand_adjustment)

    # Calculate order amount using base-stock policy
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to reduce volatility
    smoothing_factor = 0.33424491877411683  # OPT_PARAM: {"initial": 0.33424491877411683, "min": 0.3, "max": 0.6, "type": "float"}
    if pipeline_orders:
        previous_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * previous_order
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
