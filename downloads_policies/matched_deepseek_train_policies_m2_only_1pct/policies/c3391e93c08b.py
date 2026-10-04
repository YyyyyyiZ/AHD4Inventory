# policy_hash: c3391e93c08b0ccc125b960d554895d5ebad85a01e05c48376c580c0577a04e6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 21
# source_prompt_files: 1
# best_target_performance: 1123.63
# best_prompt_performance: 1123.63
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_154141.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.0  # OPT_PARAM: {"initial": 450.0, "min": 300, "max": 600, "type": "float"}
    safety_stock = 133.6382899659725  # OPT_PARAM: {"initial": 133.6382899659725, "min": 50, "max": 250, "type": "float"}
    demand_estimate = 94.44274923472857  # OPT_PARAM: {"initial": 94.44274923472857, "min": 80, "max": 120, "type": "float"}
    max_order = 99.44473830496588  # OPT_PARAM: {"initial": 99.44473830496588, "min": 80, "max": 200, "type": "float"}
    min_order = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand over lead time plus one period
    expected_demand = demand_estimate * (len(pipeline_orders) + 1)

    # Calculate target inventory position
    target_position = expected_demand + safety_stock

    # Calculate base order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply smoothing: order at least min_order if below target
    if order_amount > 0:
        order_amount = max(min_order, order_amount)

    # Cap order amount
    order_amount = min(order_amount, max_order)

    # Round to nearest integer
    return order_amount
