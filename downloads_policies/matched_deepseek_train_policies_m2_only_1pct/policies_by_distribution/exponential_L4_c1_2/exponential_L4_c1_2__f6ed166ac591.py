# policy_hash: f6ed166ac5911d8d1a0ec885d50b6329bbef6273f3daf072ebac06b3f3a75290
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 6924.8
# best_prompt_performance: 6924.78
# best_rel_error_pct: 0.000289
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_034811.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 265.22907062738716  # OPT_PARAM: {"initial": 265.22907062738716, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 32.265615543776434  # OPT_PARAM: {"initial": 32.265615543776434, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.2794188958417118  # OPT_PARAM: {"initial": 0.2794188958417118, "min": 0.1, "max": 2.0, "type": "float"}
    pipeline_weight = 1.1963860348624307  # OPT_PARAM: {"initial": 1.1963860348624307, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate pipeline-adjusted inventory position
    pipeline_sum = sum(pipeline_orders)
    inventory_position = on_hand_inventory + pipeline_sum

    # Calculate forecasted demand (using recent pipeline arrivals as proxy)
    recent_demand_estimate = 0
    if len(pipeline_orders) > 0:
        # Use average of recent pipeline orders as demand estimate
        recent_demand_estimate = sum(pipeline_orders) / len(pipeline_orders)

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * recent_demand_estimate

    # Calculate target inventory position
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount with pipeline consideration
    order_amount = max(0, target_inventory - on_hand_inventory - pipeline_weight * pipeline_sum)

    # Round to nearest integer (since order amount should be integer)
    return order_amount
