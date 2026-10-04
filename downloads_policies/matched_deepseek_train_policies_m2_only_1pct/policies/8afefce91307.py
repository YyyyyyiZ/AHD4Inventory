# policy_hash: 8afefce91307fbc627f7a022fa2c17ddf45ba6e3a109a2be64c3435108e88783
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 11266.74
# best_prompt_performance: 11268.56
# best_rel_error_pct: 0.016154
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_005308.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 403.7753396407421  # OPT_PARAM: {"initial": 403.7753396407421, "min": 200, "max": 800, "type": "float"}
    safety_stock = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 50, "max": 300, "type": "float"}
    demand_forecast_factor = 3.6775178207854093e-13  # OPT_PARAM: {"initial": 3.6775178207854093e-13, "min": 0.0, "max": 0.6, "type": "float"}
    smoothing_factor = 0.07642163714908055  # OPT_PARAM: {"initial": 0.07642163714908055, "min": 0.05, "max": 0.5, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 1.0, "type": "float"}
    lead_time_coverage = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    # Use weighted average of recent pipeline orders as demand proxy
    if len(pipeline_orders) >= 2:
        recent_demand_estimate = (pipeline_orders[0] + pipeline_orders[1]) / 2
    else:
        recent_demand_estimate = pipeline_orders[0] if pipeline_orders else 0

    # Calculate target inventory position
    expected_demand_during_leadtime = recent_demand_estimate * lead_time_coverage * len(pipeline_orders)
    target_inventory = base_stock + demand_forecast_factor * expected_demand_during_leadtime

    # Ensure minimum safety stock
    order_up_to = max(target_inventory, safety_stock)

    # Calculate raw order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing
    if pipeline_orders:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
    else:
        smoothed_order = raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
