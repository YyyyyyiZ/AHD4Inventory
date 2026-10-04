# policy_hash: 187b13821c79e8e9c27bc741370f7a182eba684f1796cddd9130c4cae99946d0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2353.7
# best_prompt_performance: 2358.34
# best_rel_error_pct: 0.197136
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_185408.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 716.2876532605757  # OPT_PARAM: {"initial": 716.2876532605757, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 68.38792773698275  # OPT_PARAM: {"initial": 68.38792773698275, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.3491888297912532  # OPT_PARAM: {"initial": 0.3491888297912532, "min": 0.1, "max": 0.9, "type": "float"}
    demand_forecast_factor = 0.9941053264369183  # OPT_PARAM: {"initial": 0.9941053264369183, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_weight = 0.4332512767089379  # OPT_PARAM: {"initial": 0.4332512767089379, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = base_stock + safety_stock

    # Estimate upcoming demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    recent_arrivals = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust target based on demand forecast
    adjusted_target = target_inventory + demand_forecast_factor * avg_recent_demand

    # Consider pipeline composition when ordering
    # Give more weight to reducing order variability
    pipeline_variability = max(pipeline_orders) - min(pipeline_orders) if pipeline_orders else 0
    stability_adjustment = pipeline_weight * pipeline_variability

    # Smooth ordering with stability consideration
    raw_order = adjusted_target - inventory_position - stability_adjustment
    order_amount = max(0, smoothing_factor * raw_order)

    # Round to nearest integer since order amount should be integer
    return order_amount
