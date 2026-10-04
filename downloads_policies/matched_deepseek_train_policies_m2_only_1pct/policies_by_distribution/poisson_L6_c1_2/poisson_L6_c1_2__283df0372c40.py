# policy_hash: 283df0372c4096213ca2e48c615b89d3e0efbb496b0f822310714e69102d17c2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 1031.1
# best_prompt_performance: 1031.26
# best_rel_error_pct: 0.015517
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_013112.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 479.9752252141709  # OPT_PARAM: {"initial": 479.9752252141709, "min": 300, "max": 600, "type": "float"}
    safety_stock = 121.9782825300081  # OPT_PARAM: {"initial": 121.9782825300081, "min": 50, "max": 150, "type": "float"}
    demand_estimate = 110.0  # OPT_PARAM: {"initial": 110.0, "min": 90, "max": 110, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * lead_time

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(0, target_position - inventory_position)

    # Apply adjustment factor with pipeline consideration
    pipeline_coverage = sum(pipeline_orders) / max(1, expected_lead_time_demand)
    max_order = base_stock * adjustment_factor * (1.0 - pipeline_weight * max(0, 1.0 - pipeline_coverage))

    # Final order amount
    order_amount = min(order_up_to, max_order)

    return order_amount
