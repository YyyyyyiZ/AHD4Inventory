# policy_hash: 00a17b29d235c7548543ac7b9541d6b9fd8d0da2fe855afe2f6e574a802eebf8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 1052.46
# best_prompt_performance: 1052.46
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_021643.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 294.00000004771687  # OPT_PARAM: {"initial": 294.00000004771687, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 200.0  # OPT_PARAM: {"initial": 200.0, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 50, "max": 150, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - net_inventory)

    # Apply base stock as upper bound
    order_amount = min(order_amount, max(0, base_stock - net_inventory))

    return order_amount
