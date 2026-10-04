# policy_hash: 6ccb3a57aaa9513605e4c44a791e3145a9dfbaaec2b8d444935846993ff4251a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1738.82
# best_prompt_performance: 1738.82
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_033700.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 246.66217566894335  # OPT_PARAM: {"initial": 246.66217566894335, "min": 100, "max": 400, "type": "float"}
    safety_stock = 2.7321973229512255  # OPT_PARAM: {"initial": 2.7321973229512255, "min": 0, "max": 50, "type": "float"}
    demand_forecast = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with smoothing
    lead_time = len(pipeline_orders)
    expected_demand_during_leadtime = demand_forecast * lead_time

    # Adjust target based on pipeline variability
    pipeline_variability = max(0, sum(pipeline_orders) - demand_forecast * lead_time)
    adjustment = smoothing_factor * pipeline_variability

    # Calculate target inventory position
    target_position = base_stock + safety_stock + expected_demand_during_leadtime - adjustment

    # Order up to target, but not less than 0
    order_amount = max(0, target_position - inventory_position)

    # Round to nearest integer since demand is integer
    order_amount = int(round(order_amount))

    return order_amount
