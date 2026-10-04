# policy_hash: a78c1188b07b2801b8cc11b35eae4fdb2886a727fde461d49e96aa59285ad831
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 38
# source_prompt_files: 1
# best_target_performance: 6244.26
# best_prompt_performance: 6244.26
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_030909.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 687.9098938403151  # OPT_PARAM: {"initial": 687.9098938403151, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 260.186962595713  # OPT_PARAM: {"initial": 260.186962595713, "min": 0, "max": 300, "type": "float"}
    demand_estimate = 94.16443488732173  # OPT_PARAM: {"initial": 94.16443488732173, "min": 50, "max": 200, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Cap order amount to avoid excessive ordering
    max_order = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 4.0, "type": "float"}
    order_amount = min(order_amount, max_order * demand_estimate)

    return order_amount
