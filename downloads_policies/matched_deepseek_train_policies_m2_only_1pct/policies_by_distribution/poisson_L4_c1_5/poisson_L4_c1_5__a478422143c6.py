# policy_hash: a478422143c6302e08fb4e7c9e434a1162ee2b13ebc4b4d3ca0c300496293c8e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1123.6
# best_prompt_performance: 1123.6
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_155518.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 480.0  # OPT_PARAM: {"initial": 480.0, "min": 300, "max": 600, "type": "float"}
    safety_stock = 167.40193652486008  # OPT_PARAM: {"initial": 167.40193652486008, "min": 50, "max": 250, "type": "float"}
    demand_estimate = 86.05376645072408  # OPT_PARAM: {"initial": 86.05376645072408, "min": 80, "max": 120, "type": "float"}
    max_order = 99.44783911845121  # OPT_PARAM: {"initial": 99.44783911845121, "min": 80, "max": 200, "type": "float"}
    min_order = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 50, "type": "float"}

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
