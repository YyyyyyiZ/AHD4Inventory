# policy_hash: fb14c4eedf6fc8eb66a95c555b4b8d6e8cd5ac4d9f86b9631a7472e156e20a60
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 745.4
# best_prompt_performance: 745.8
# best_rel_error_pct: 0.053662
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_101725.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 444.66178752350936  # OPT_PARAM: {"initial": 444.66178752350936, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 11.740068502379787  # OPT_PARAM: {"initial": 11.740068502379787, "min": 0, "max": 200, "type": "float"}
    forecast_horizon = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 10, "type": "int"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecasting using historical average (approximated)
    # Since we can't access historical data, we use a fixed forecast value
    # This would be optimized during training
    forecast_demand = 60.800402070051454  # OPT_PARAM: {"initial": 60.800402070051454, "min": 50, "max": 150, "type": "float"}

    # Calculate expected demand over lead time + forecast horizon
    expected_demand = forecast_demand * (len(pipeline_orders) + forecast_horizon)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock + smoothing_factor * expected_demand

    # Calculate order amount
    order_amount = max(0, target_inventory - net_inventory)

    # Apply ordering constraints
    min_order = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 50, "type": "float"}
    max_order = 96.40008082120738  # OPT_PARAM: {"initial": 96.40008082120738, "min": 50, "max": 500, "type": "float"}

    if order_amount < min_order:
        order_amount = 0
    elif order_amount > max_order:
        order_amount = max_order

    return order_amount
