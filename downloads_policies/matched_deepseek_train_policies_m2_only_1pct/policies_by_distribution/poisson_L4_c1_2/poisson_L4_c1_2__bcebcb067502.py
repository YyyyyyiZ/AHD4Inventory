# policy_hash: bcebcb0675023e44b11a8bc2eb93f9897b87296a490783ba06140bb0f3918bce
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 1957.74
# best_prompt_performance: 1957.74
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_033537.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.0  # OPT_PARAM: {"initial": 450.0, "min": 300, "max": 600, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 20, "max": 150, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 80, "max": 120, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand over lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, target_position)

    # Calculate order amount
    order_amount = max(0, order_up_to - net_inventory)

    # Round to nearest integer (since order amount must be integer)
    order_amount = int(round(order_amount))

    return order_amount
