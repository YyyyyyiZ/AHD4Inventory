# policy_hash: d7593335506461adab64b979249dfdf357f725ef51fc76df4b414878c9cd2d3b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2395.09
# best_prompt_performance: 2380.98
# best_rel_error_pct: 0.589122
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_041622.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 502.2285278750766  # OPT_PARAM: {"initial": 502.2285278750766, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, target_inventory)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to reduce order volatility
    if len(pipeline_orders) > 0 and pipeline_orders[-1] > 0:
        previous_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * previous_order
        order_amount = max(0, int(round(smoothed_order)))
    else:
        order_amount = max(0, int(round(order_amount)))

    return order_amount
