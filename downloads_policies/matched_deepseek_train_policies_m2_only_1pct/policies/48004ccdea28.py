# policy_hash: 48004ccdea28bc258bc1086c3b60ad3672c8a53cf7718bc166e6aba7f4d60bfa
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 1035.94
# best_prompt_performance: 1035.94
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_000151.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 453.12459249339304  # OPT_PARAM: {"initial": 453.12459249339304, "min": 300, "max": 500, "type": "float"}
    safety_stock = 63.12459249339368  # OPT_PARAM: {"initial": 63.12459249339368, "min": 30, "max": 100, "type": "float"}
    demand_forecast = 96.09650044229139  # OPT_PARAM: {"initial": 96.09650044229139, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    lost_sales_weight = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 1.0, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Adjust safety stock based on cost ratio
    adjusted_safety_stock = safety_stock * lost_sales_weight

    # Calculate target inventory level
    target_inventory = base_stock + adjusted_safety_stock - pipeline_weight * expected_lead_time_demand

    # Calculate order-up-to quantity
    order_up_to = target_inventory - inventory_position

    # Apply smoothing with demand forecast as baseline
    if order_up_to > 0:
        smoothed_order = smoothing_factor * order_up_to + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = max(0, smoothing_factor * order_up_to)

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
