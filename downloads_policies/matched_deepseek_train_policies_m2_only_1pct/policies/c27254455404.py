# policy_hash: c272544554048004a1516d765463d9291435455f9aadc22d99212c6158fda0d5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1597.98
# best_prompt_performance: 1599.1
# best_rel_error_pct: 0.070088
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_011550.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 449.6913590376331  # OPT_PARAM: {"initial": 449.6913590376331, "min": 400, "max": 700, "type": "float"}
    safety_stock = 82.05087562513704  # OPT_PARAM: {"initial": 82.05087562513704, "min": 40, "max": 120, "type": "float"}
    demand_estimate = 115.92831255349388  # OPT_PARAM: {"initial": 115.92831255349388, "min": 80, "max": 120, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with pipeline consideration
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Adjust target based on pipeline status
    pipeline_coverage = sum(pipeline_orders) / max(1, expected_lead_time_demand)
    adjusted_safety = safety_stock * (1.0 + (1.0 - pipeline_weight) * (1.0 - pipeline_coverage))

    # Calculate target inventory position
    target_position = expected_lead_time_demand + adjusted_safety

    # Calculate base order amount
    order_amount = max(0, target_position - inventory_position)

    # Smooth adjustment with pipeline-aware cap
    if order_amount > 0:
        max_order = base_stock * adjustment_factor * (1.0 + pipeline_weight * (1.0 - pipeline_coverage))
        order_amount = min(order_amount, max_order)

    return order_amount
