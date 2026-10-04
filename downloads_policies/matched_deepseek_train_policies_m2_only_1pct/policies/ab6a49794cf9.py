# policy_hash: ab6a49794cf92578c4ca59a15d9e995fbfe36589fc0075a7869ab14a13ca79a9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 1091.5
# best_prompt_performance: 1091.85
# best_rel_error_pct: 0.032066
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_012938.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 300.0  # OPT_PARAM: {"initial": 300.0, "min": 300, "max": 600, "type": "float"}
    safety_stock = 149.9  # OPT_PARAM: {"initial": 149.9, "min": 50, "max": 150, "type": "float"}
    demand_estimate = 106.91462814651159  # OPT_PARAM: {"initial": 106.91462814651159, "min": 90, "max": 110, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Adjust safety stock based on pipeline coverage
    pipeline_coverage = sum(pipeline_orders) / max(1, expected_lead_time_demand)
    adjusted_safety = safety_stock * (1.0 + (1.0 - pipeline_weight) * (1.0 - pipeline_coverage))

    # Calculate target inventory position
    target_position = expected_lead_time_demand + adjusted_safety

    # Calculate base order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply smoothing with adjustment factor
    if order_amount > 0:
        max_order = base_stock * adjustment_factor * (1.0 + pipeline_weight * (1.0 - pipeline_coverage))
        order_amount = min(order_amount, max_order)

    return order_amount
