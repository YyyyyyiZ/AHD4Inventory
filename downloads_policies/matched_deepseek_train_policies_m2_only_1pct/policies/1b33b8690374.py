# policy_hash: 1b33b8690374b8c3b90e7f05b3a45d3a394976e80fb935366bb5a0b841b9aaf2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 27
# source_prompt_files: 1
# best_target_performance: 1169.04
# best_prompt_performance: 1169.04
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_021201.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 698.0997255235969  # OPT_PARAM: {"initial": 698.0997255235969, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 74.14773438874496  # OPT_PARAM: {"initial": 74.14773438874496, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 127.4132721440891  # OPT_PARAM: {"initial": 127.4132721440891, "min": 50, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Cap order amount to avoid excessive ordering
    max_order = 98.9890884084336  # OPT_PARAM: {"initial": 98.9890884084336, "min": 50, "max": 500, "type": "float"}
    order_amount = min(order_amount, max_order)

    # Round to nearest integer since demand is integer
    order_amount = int(round(order_amount))

    return order_amount
