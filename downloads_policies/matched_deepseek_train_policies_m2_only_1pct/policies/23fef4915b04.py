# policy_hash: 23fef4915b04742ec80a221f9d45896e0f741f699d769e326f5532f88f21310d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 26
# source_prompt_files: 2
# best_target_performance: 5938.1
# best_prompt_performance: 5937.88
# best_rel_error_pct: 0.003705
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_024157.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 180.09737785342998  # OPT_PARAM: {"initial": 180.09737785342998, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 28.595486835854985  # OPT_PARAM: {"initial": 28.595486835854985, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 99.89761755917773  # OPT_PARAM: {"initial": 99.89761755917773, "min": 10, "max": 500, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand coverage
    expected_demand_coverage = demand_estimate * len(pipeline_orders)

    # Adjust base stock based on pipeline status
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order-up-to level considering pipeline
    order_up_to = max(adjusted_base_stock, expected_demand_coverage)

    # Calculate order amount with smoothing
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid extreme fluctuations
    smoothing_factor = 0.5937194153036451  # OPT_PARAM: {"initial": 0.5937194153036451, "min": 0.1, "max": 1.0, "type": "float"}
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
