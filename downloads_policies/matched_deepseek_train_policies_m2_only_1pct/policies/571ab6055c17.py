# policy_hash: 571ab6055c174c283eeeafa1227088c901b178851157e8728b692cdb39360c0b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 902.34
# best_prompt_performance: 900.47
# best_rel_error_pct: 0.207239
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_075929.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 485.07930717121985  # OPT_PARAM: {"initial": 485.07930717121985, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 99.37677569181204  # OPT_PARAM: {"initial": 99.37677569181204, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = 4 * demand_forecast

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, target_position)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid large order fluctuations
    if order_amount > 2 * demand_forecast:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast

    return order_amount
