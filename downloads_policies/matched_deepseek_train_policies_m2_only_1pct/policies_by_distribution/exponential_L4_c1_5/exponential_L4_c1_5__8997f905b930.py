# policy_hash: 8997f905b930b26ae68b74c13f956feb5152e9510653cf1af56f28578004761e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 18
# source_prompt_files: 1
# best_target_performance: 12085.93
# best_prompt_performance: 12085.93
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_003320.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 550.0  # OPT_PARAM: {"initial": 550.0, "min": 300, "max": 800, "type": "float"}
    safety_stock = 177.61913055445865  # OPT_PARAM: {"initial": 177.61913055445865, "min": 100, "max": 300, "type": "float"}
    demand_estimate = 129.38591276729824  # OPT_PARAM: {"initial": 129.38591276729824, "min": 100, "max": 200, "type": "float"}
    adjustment_factor = 0.6990277129791289  # OPT_PARAM: {"initial": 0.6990277129791289, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with adjustment
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders) * adjustment_factor

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply base stock as upper bound with smoother adjustment
    if inventory_position < base_stock:
        order_amount = min(order_amount, base_stock - inventory_position)
    else:
        order_amount = 0

    return order_amount
