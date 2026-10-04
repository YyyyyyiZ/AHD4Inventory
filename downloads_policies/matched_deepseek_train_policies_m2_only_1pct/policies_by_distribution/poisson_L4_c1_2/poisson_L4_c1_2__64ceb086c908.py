# policy_hash: 64ceb086c908cde01fd68da1956c2ad267751efe7c9360157b07f83b9536b2a2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 1370.4
# best_prompt_performance: 1374.76
# best_rel_error_pct: 0.318155
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_034308.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.1280289506735  # OPT_PARAM: {"initial": 450.1280289506735, "min": 300, "max": 500, "type": "float"}
    safety_stock = 95.00000164353213  # OPT_PARAM: {"initial": 95.00000164353213, "min": 50, "max": 150, "type": "float"}
    demand_estimate = 85.0  # OPT_PARAM: {"initial": 85.0, "min": 85, "max": 115, "type": "float"}
    smoothing_factor = 0.05000000000302451  # OPT_PARAM: {"initial": 0.05000000000302451, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.2, "type": "float"}
    demand_smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate inventory position with full pipeline weight
    inventory_position = on_hand_inventory + sum(pipeline_orders) * pipeline_weight

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position with smoothing
    target_inventory = smoothing_factor * (expected_lead_time_demand + safety_stock) + (1 - smoothing_factor) * base_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply demand-smoothing adjustment
    smoothed_order = demand_smoothing * order_amount + (1 - demand_smoothing) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
