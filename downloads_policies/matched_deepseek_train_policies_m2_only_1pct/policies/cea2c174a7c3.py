# policy_hash: cea2c174a7c36cf87d549cb707b0dc937de4930ca8da3ac8e2657a1ada1e5716
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 3336.9
# best_prompt_performance: 3336.9
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_093638.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 400.0  # OPT_PARAM: {"initial": 400.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 133.32975933347413  # OPT_PARAM: {"initial": 133.32975933347413, "min": 40, "max": 150, "type": "float"}
    demand_forecast = 113.13360903718659  # OPT_PARAM: {"initial": 113.13360903718659, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with smoothing
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory position with dynamic adjustment
    target_inventory = expected_lead_time_demand + safety_stock

    # Apply smoothing to order amount to reduce volatility
    order_amount_raw = max(0, target_inventory - inventory_position)
    order_amount = smoothing_factor * order_amount_raw + (1 - smoothing_factor) * min(order_amount_raw, base_stock)

    # Round to nearest integer (since demands are integers)
    return order_amount
