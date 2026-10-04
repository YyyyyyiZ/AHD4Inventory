# policy_hash: 8add9bf3415b270c827ea0cfab22acfb7d84bcf935dd0e9a94da69be4b6a84f1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1427.12
# best_prompt_performance: 1427.12
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_230831.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 310.37578353996327  # OPT_PARAM: {"initial": 310.37578353996327, "min": 200, "max": 400, "type": "float"}
    safety_stock = 176.6212365678386  # OPT_PARAM: {"initial": 176.6212365678386, "min": 50, "max": 200, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with smoothing
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position with dynamic adjustment
    target_position = expected_lead_time_demand + safety_stock

    # Calculate order amount with smoothing
    raw_order = max(0, target_position - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * max(0, base_stock - inventory_position)

    # Apply base stock as upper bound
    order_amount = min(smoothed_order, max(0, base_stock - inventory_position))

    return order_amount
