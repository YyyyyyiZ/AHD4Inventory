# policy_hash: 203ab76dfc814c420157165ae62f3713c12b9dec988439fd9f275a1f607249de
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 11647.45
# best_prompt_performance: 11647.45
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_231037.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 324.93124999998804  # OPT_PARAM: {"initial": 324.93124999998804, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    pipeline_variance = sum((q - sum(pipeline_orders)/len(pipeline_orders))**2 for q in pipeline_orders) if pipeline_orders else 0
    pipeline_risk_factor = 1.0 + min(0.5, pipeline_variance / 10000)  # OPT_PARAM: {"initial": 10000, "min": 1000, "max": 50000, "type": "float"}

    # Dynamic target based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    dynamic_adjustment = demand_forecast_factor * recent_arrivals

    # Calculate target inventory level
    target_inventory = base_stock * pipeline_risk_factor + safety_stock + dynamic_adjustment

    # Calculate order amount with smoothing
    raw_order = max(0, target_inventory - inventory_position)
    smoothing_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.1, "max": 1.0, "type": "float"}

    # Consider upcoming arrivals in next period
    next_arrival = pipeline_orders[1] if len(pipeline_orders) > 1 else 0
    order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * next_arrival

    # Round to integer (as required by output type)
    return order_amount
