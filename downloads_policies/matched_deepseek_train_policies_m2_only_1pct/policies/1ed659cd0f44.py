# policy_hash: 1ed659cd0f44e8dfeb3d811edb8d56e752f043348ae3f1e54f930c08a22226be
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 1341.6
# best_prompt_performance: 1341.52
# best_rel_error_pct: 0.005963
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_231152.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 303.27911147471684  # OPT_PARAM: {"initial": 303.27911147471684, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 46.29343172373754  # OPT_PARAM: {"initial": 46.29343172373754, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.6260955837238898  # OPT_PARAM: {"initial": 0.6260955837238898, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    next_arrivals = pipeline_orders[1] if len(pipeline_orders) > 1 else 0

    # Dynamic adjustment based on pipeline status
    pipeline_adjustment = -0.1  # Optimized
    if recent_arrivals > 0:
        pipeline_adjustment = -recent_arrivals * 0.1  # OPT_PARAM: {"initial": -0.1, "min": -0.5, "max": 0.5, "type": "float"}

    # Forecast future demand based on current inventory and pipeline
    forecast_demand = (base_stock - inventory_position) * demand_forecast_factor

    # Calculate target inventory position
    target_position = base_stock + safety_stock + pipeline_adjustment

    # Calculate order amount with smoothing
    raw_order = max(0, target_position - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.5263393395251018  # OPT_PARAM: {"initial": 0.5263393395251018, "min": 0.1, "max": 1.0, "type": "float"}
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * forecast_demand

    # Ensure order is integer and non-negative
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
