# policy_hash: 086267a558ed10b0f1cd022ff2422436db4c5d257ca77808bb514fd923229081
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 40
# source_prompt_files: 1
# best_target_performance: 744.84
# best_prompt_performance: 744.84
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260127_224553.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 483.02171902112065  # OPT_PARAM: {"initial": 483.02171902112065, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 65.21700237797218  # OPT_PARAM: {"initial": 65.21700237797218, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 143.59610714176878  # OPT_PARAM: {"initial": 143.59610714176878, "min": 50, "max": 150, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Cap the order amount to avoid excessive ordering
    max_order = 96.25025381291438  # OPT_PARAM: {"initial": 96.25025381291438, "min": 50, "max": 400, "type": "float"}
    order_amount = min(order_amount, max_order)

    return order_amount
