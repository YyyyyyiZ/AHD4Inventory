# policy_hash: fbc2b3ef85c44759dd66b18347850aa01542be9b56f7f209842433f52e352424
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 36
# source_prompt_files: 1
# best_target_performance: 778.52
# best_prompt_performance: 781.36
# best_rel_error_pct: 0.364795
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_002647.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 414.82916227867844  # OPT_PARAM: {"initial": 414.82916227867844, "min": 350, "max": 500, "type": "float"}
    demand_estimate = 97.04641364047012  # OPT_PARAM: {"initial": 97.04641364047012, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    safety_stock = 27.077307598911492  # OPT_PARAM: {"initial": 27.077307598911492, "min": 10, "max": 60, "type": "float"}
    pipeline_weight = 0.4520654972596582  # OPT_PARAM: {"initial": 0.4520654972596582, "min": 0.3, "max": 1.0, "type": "float"}
    min_order_fraction = 0.30111895742682815  # OPT_PARAM: {"initial": 0.30111895742682815, "min": 0.1, "max": 0.8, "type": "float"}
    threshold_factor = 0.7593324043083977  # OPT_PARAM: {"initial": 0.7593324043083977, "min": 0.5, "max": 1.0, "type": "float"}
    pipeline_leadtime_adjust = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight**(i+1) for i, p in enumerate(pipeline_orders))
    effective_position = on_hand_inventory + weighted_pipeline

    # Adjust base stock for lead time
    adjusted_base = base_stock * pipeline_leadtime_adjust

    # Dynamic target based on safety stock
    target_position = adjusted_base + safety_stock

    # Order amount calculation
    order_amount = max(0, target_position - effective_position)

    # Apply smoothing with demand-based adjustment
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Ensure minimum order when inventory is low
    if effective_position < base_stock * threshold_factor:
        order_amount = max(order_amount, demand_estimate * min_order_fraction)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
