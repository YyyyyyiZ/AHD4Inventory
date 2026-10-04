# policy_hash: a15e4f2b42af32c28ab0e72b34a4c6aa743246857cbe2485d969e3d0bb8977a5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 31
# source_prompt_files: 1
# best_target_performance: 3813.78
# best_prompt_performance: 3813.84
# best_rel_error_pct: 0.001573
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_235447.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 411.6414665325511  # OPT_PARAM: {"initial": 411.6414665325511, "min": 400, "max": 650, "type": "float"}
    safety_stock = 60.00000040383058  # OPT_PARAM: {"initial": 60.00000040383058, "min": 60, "max": 130, "type": "float"}
    demand_forecast_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.9, "max": 1.2, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.01, "max": 0.2, "type": "float"}
    recent_periods = 6  # OPT_PARAM: {"initial": 6, "min": 4, "max": 10, "type": "int"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand from recent pipeline orders
    if len(pipeline_orders) > 0:
        # Use configurable number of recent periods for demand forecasting
        recent_orders = pipeline_orders[-recent_periods:] if len(pipeline_orders) >= recent_periods else pipeline_orders
        expected_demand = sum(recent_orders) / len(recent_orders)
    else:
        expected_demand = 0

    # Adjust base stock with weighted pipeline consideration
    pipeline_contribution = sum(pipeline_orders) * pipeline_weight / len(pipeline_orders) if pipeline_orders else 0
    adjusted_base_stock = base_stock + safety_stock + (expected_demand * demand_forecast_factor) + pipeline_contribution

    # Calculate raw order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing with expected demand
    smoothed_order = raw_order * smoothing_factor + (1 - smoothing_factor) * expected_demand

    # Ensure order is non-negative integer
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
