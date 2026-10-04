# policy_hash: 1f4c33b8062959accd65569c27b6ff2da205cac5cc0905c1992935c862524e40
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 815.08
# best_prompt_performance: 812.28
# best_rel_error_pct: 0.343525
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_013418.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 508.70670535832875  # OPT_PARAM: {"initial": 508.70670535832875, "min": 400, "max": 800, "type": "float"}
    safety_stock = 33.70670535832825  # OPT_PARAM: {"initial": 33.70670535832825, "min": 20, "max": 200, "type": "float"}
    demand_estimate = 93.55060416243616  # OPT_PARAM: {"initial": 93.55060416243616, "min": 70, "max": 130, "type": "float"}
    adjustment_factor = 0.9911850721101413  # OPT_PARAM: {"initial": 0.9911850721101413, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.3, "type": "float"}
    order_threshold = 0.7549600092097698  # OPT_PARAM: {"initial": 0.7549600092097698, "min": 0.5, "max": 1.5, "type": "float"}
    demand_adj_factor = 0.9027924878368366  # OPT_PARAM: {"initial": 0.9027924878368366, "min": 0.8, "max": 1.1, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand over lead time with adjustment
    expected_demand_over_lead_time = demand_estimate * len(pipeline_orders) * demand_adj_factor

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock - adjustment_factor * (expected_demand_over_lead_time - demand_estimate * 6)

    # Calculate base order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Only place orders when inventory position is significantly below target
    if order_amount > 0 and (target_inventory - inventory_position) > order_threshold * demand_estimate:
        # Apply smoothing with stronger effect for larger gaps
        gap_ratio = (target_inventory - inventory_position) / target_inventory
        effective_smoothing = smoothing_factor * (1 + gap_ratio)
        order_amount = effective_smoothing * order_amount + (1 - effective_smoothing) * demand_estimate
    elif order_amount > 0:
        # Small gaps: order exactly the gap
        order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
