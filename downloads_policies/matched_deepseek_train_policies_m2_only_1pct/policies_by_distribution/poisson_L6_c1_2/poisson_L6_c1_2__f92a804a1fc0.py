# policy_hash: f92a804a1fc0dbd49307c1f062956ea4755d25c67081a56e2d3f27c4140a09b1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 36
# source_prompt_files: 1
# best_target_performance: 1327.86
# best_prompt_performance: 1327.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_011415.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 520.0065647432843  # OPT_PARAM: {"initial": 520.0065647432843, "min": 400, "max": 800, "type": "float"}
    safety_stock = 40.00656474328439  # OPT_PARAM: {"initial": 40.00656474328439, "min": 20, "max": 200, "type": "float"}
    demand_estimate = 98.04801762159256  # OPT_PARAM: {"initial": 98.04801762159256, "min": 70, "max": 130, "type": "float"}
    adjustment_factor = 0.7019668699186747  # OPT_PARAM: {"initial": 0.7019668699186747, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand over lead time
    expected_demand_over_lead_time = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position with adjustment
    target_inventory = base_stock + safety_stock - adjustment_factor * (expected_demand_over_lead_time - demand_estimate * 6)

    # Smooth the order amount to reduce volatility
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid large order swings
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
