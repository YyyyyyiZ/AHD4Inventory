# policy_hash: f57168eb3399b690543a46960614342d3428c94a0b7eaacc1dc7bb2bf3f1d5db
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 811.84
# best_prompt_performance: 811.84
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_040557.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 373.88324356117795  # OPT_PARAM: {"initial": 373.88324356117795, "min": 350, "max": 420, "type": "float"}
    safety_stock = 70.0  # OPT_PARAM: {"initial": 70.0, "min": 70, "max": 110, "type": "float"}
    demand_estimate = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.9228740277696146  # OPT_PARAM: {"initial": 0.9228740277696146, "min": 0.8, "max": 1.2, "type": "float"}
    lead_time = 4

    # Calculate inventory position with weighted pipeline
    inventory_position = on_hand_inventory + sum(pipeline_orders) * pipeline_weight

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock

    # Calculate order amount needed to reach target
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing with demand estimate as baseline
    smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Ensure order is at least demand estimate when significantly below target
    if inventory_position < target_inventory - demand_estimate:
        smoothed_order = max(smoothed_order, demand_estimate)

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
