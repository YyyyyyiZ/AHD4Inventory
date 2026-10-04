# policy_hash: ce208f1463d55c41f01b3a6276fa82be646c1c93e3a265f2be96dcd4302de36d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 782.14
# best_prompt_performance: 782.16
# best_rel_error_pct: 0.002557
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_013248.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 625.0  # OPT_PARAM: {"initial": 625.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 89.63297462043215  # OPT_PARAM: {"initial": 89.63297462043215, "min": 30, "max": 120, "type": "float"}
    demand_estimate = 119.7345732121946  # OPT_PARAM: {"initial": 119.7345732121946, "min": 80, "max": 120, "type": "float"}
    max_order = 94.96720457272498  # OPT_PARAM: {"initial": 94.96720457272498, "min": 80, "max": 200, "type": "float"}
    min_order = 18.407064913811965  # OPT_PARAM: {"initial": 18.407064913811965, "min": 0, "max": 50, "type": "float"}
    smoothing_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.1, "max": 1.0, "type": "float"}
    lead_time_factor = 1.3  # OPT_PARAM: {"initial": 1.3, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with adjustment factor
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders) * lead_time_factor

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate base order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply smoothing: blend with previous order if pipeline not empty
    if pipeline_orders and pipeline_orders[-1] > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * pipeline_orders[-1]

    # Apply order constraints
    order_amount = min(order_amount, max_order)
    order_amount = max(order_amount, min_order)

    # Round to nearest integer since order amount must be integer
    return order_amount
