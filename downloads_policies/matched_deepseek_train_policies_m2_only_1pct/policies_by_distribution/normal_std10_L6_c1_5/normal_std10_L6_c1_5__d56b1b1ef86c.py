# policy_hash: d56b1b1ef86c8e8e8140d3a55089c37d9782ed1d754f08e2d820fb15c993c558
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 1834.02
# best_prompt_performance: 1833.8
# best_rel_error_pct: 0.011996
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_202009.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 643.3392552866779  # OPT_PARAM: {"initial": 643.3392552866779, "min": 400, "max": 900, "type": "float"}
    safety_stock = 24.840499199244856  # OPT_PARAM: {"initial": 24.840499199244856, "min": 0, "max": 100, "type": "float"}
    demand_forecast = 98.68674744456224  # OPT_PARAM: {"initial": 98.68674744456224, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.1, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simpler pipeline adjustment - less aggressive than original
    recent_arrivals = pipeline_orders[0] if len(pipeline_orders) > 0 else 0
    pipeline_adjustment = max(0.9, min(1.1, 1.0 - pipeline_weight * recent_arrivals / demand_forecast))

    # Adjusted base stock
    adjusted_base_stock = base_stock * pipeline_adjustment + safety_stock

    # Calculate order-up-to level
    order_up_to = adjusted_base_stock - inventory_position

    # Apply smoothing only when ordering
    if order_up_to > 0:
        smoothed_order = smoothing_factor * order_up_to + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
