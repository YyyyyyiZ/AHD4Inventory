# policy_hash: 1233b70d43fd9c52bd67761241111b80b85385aedb64005b16e9edaef73b4bcc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 782.02
# best_prompt_performance: 781.88
# best_rel_error_pct: 0.017902
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_001442.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 369.4514948273671  # OPT_PARAM: {"initial": 369.4514948273671, "min": 350, "max": 500, "type": "float"}
    demand_estimate = 86.49378131899125  # OPT_PARAM: {"initial": 86.49378131899125, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    safety_stock = 16.482909271399727  # OPT_PARAM: {"initial": 16.482909271399727, "min": 10, "max": 60, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    min_order_fraction = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.8, "type": "float"}
    threshold_factor = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight**(i+1) for i, p in enumerate(pipeline_orders))
    effective_position = on_hand_inventory + weighted_pipeline

    # Dynamic target based on safety stock
    target_position = base_stock + safety_stock

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
