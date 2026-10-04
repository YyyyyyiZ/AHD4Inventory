# policy_hash: ce81fe6640e75c6b334bf2e3420049c70fd238d225a0ee6544594ebb31241bb2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 778.84
# best_prompt_performance: 779.5
# best_rel_error_pct: 0.084741
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_012531.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 508.44024323783873  # OPT_PARAM: {"initial": 508.44024323783873, "min": 400, "max": 800, "type": "float"}
    safety_stock = 33.44024323783813  # OPT_PARAM: {"initial": 33.44024323783813, "min": 20, "max": 200, "type": "float"}
    demand_estimate = 95.56294677867814  # OPT_PARAM: {"initial": 95.56294677867814, "min": 70, "max": 130, "type": "float"}
    adjustment_factor = 0.9215895550600939  # OPT_PARAM: {"initial": 0.9215895550600939, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand over lead time
    expected_demand_over_lead_time = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock - adjustment_factor * (expected_demand_over_lead_time - demand_estimate * 6)

    # Calculate base order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing only when order amount is positive
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
