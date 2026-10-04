# policy_hash: 725e9b7c5d765cd3b4afcb649f4a35943f1935a4203a78f1a15a2c0666e0c854
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 10165.01
# best_prompt_performance: 10165.01
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_233627.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 436.37470224644625  # OPT_PARAM: {"initial": 436.37470224644625, "min": 300, "max": 600, "type": "float"}
    safety_stock = 13.496736238694368  # OPT_PARAM: {"initial": 13.496736238694368, "min": 0, "max": 100, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline (weighted towards recent orders)
    effective_pipeline = 0
    total_weight = 0
    for i, q in enumerate(pipeline_orders):
        weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
        effective_pipeline += q * weight
        total_weight += weight

    if total_weight > 0:
        effective_pipeline = effective_pipeline / total_weight * len(pipeline_orders)

    # Adjust target based on pipeline concentration
    pipeline_adjustment = 1.0
    if len(pipeline_orders) > 0 and sum(pipeline_orders) > 0:
        concentration = effective_pipeline / sum(pipeline_orders)
        pipeline_adjustment = 0.9 + 0.2 * concentration  # More concentrated → higher adjustment

    # Calculate target inventory position
    target = base_stock * pipeline_adjustment + safety_stock

    # Calculate order needed
    order_needed = max(0, target - inventory_position)

    # Apply smoothing
    if order_needed > 0:
        order_amount = smoothing * order_needed
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
