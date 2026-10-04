# policy_hash: 8c2b1494983e3b598a8b82b7c2ca7cf7f1b296087577da58553da7366b93d4ff
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1470.88
# best_prompt_performance: 1470.88
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_234701.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 465.22224212585917  # OPT_PARAM: {"initial": 465.22224212585917, "min": 300, "max": 600, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 20, "max": 150, "type": "float"}
    demand_estimate = 99.99354154090622  # OPT_PARAM: {"initial": 99.99354154090622, "min": 80, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected shortfall
    expected_shortfall = max(0, base_stock - inventory_position)

    # Adjust for pipeline variability - order more if pipeline is low
    pipeline_sum = sum(pipeline_orders)
    pipeline_adjustment = 0.8913460646955497  # OPT_PARAM: {"initial": 0.8913460646955497, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate final order
    order_amount = max(0, expected_shortfall + pipeline_adjustment)

    # Apply smoothing to avoid extreme orders
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Ensure order is integer
    order_amount = int(round(order_amount))

    return order_amount
