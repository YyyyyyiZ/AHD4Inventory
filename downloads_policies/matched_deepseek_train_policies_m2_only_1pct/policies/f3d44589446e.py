# policy_hash: f3d44589446e8063d18e7129639fdc797c00d6c28fcc5b7a93fda1d531cdcc27
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 11504.64
# best_prompt_performance: 11504.64
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_042928.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 553.7776779686646  # OPT_PARAM: {"initial": 553.7776779686646, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 130.68675240979059  # OPT_PARAM: {"initial": 130.68675240979059, "min": 50, "max": 300, "type": "float"}
    demand_estimate = 64.13251269880385  # OPT_PARAM: {"initial": 64.13251269880385, "min": 50, "max": 250, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, target_inventory)

    # Calculate order amount with smoothing
    raw_order = max(0, order_up_to - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_estimate

    # Round to nearest integer (as order_amount should be int)
    order_amount = int(round(smoothed_order))

    return order_amount
