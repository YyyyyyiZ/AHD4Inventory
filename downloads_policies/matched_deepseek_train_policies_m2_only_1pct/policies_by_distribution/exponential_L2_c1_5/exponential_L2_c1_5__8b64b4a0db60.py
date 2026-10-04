# policy_hash: 8b64b4a0db60be3ef792df83aba01ce752b25506e0c4a0a9bbdd820ed822a850
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 10164.86
# best_prompt_performance: 10164.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_233601.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 346.8188183723533  # OPT_PARAM: {"initial": 346.8188183723533, "min": 300, "max": 450, "type": "float"}
    safety_stock = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 15, "max": 40, "type": "float"}
    pipeline_weight = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.8, "type": "float"}
    lost_sales_weight = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 2.0, "type": "float"}

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

    # Simplified pipeline adjustment
    pipeline_adjustment = 1.0
    if len(pipeline_orders) > 0 and sum(pipeline_orders) > 0:
        concentration = effective_pipeline / sum(pipeline_orders)
        pipeline_adjustment = 0.8 + 0.4 * concentration

    # Calculate target with stronger lost-sales emphasis
    target = base_stock * pipeline_adjustment + safety_stock * lost_sales_weight

    # Calculate order needed
    order_needed = max(0, target - inventory_position)

    # Apply smoothing
    if order_needed > 0:
        order_amount = smoothing * order_needed
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
