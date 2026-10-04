# policy_hash: 1d99b564a1acb79b4f6cb27a8ec8ed014c89d2d919ae9094c75715df3e988d1a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 10165.44
# best_prompt_performance: 10165.44
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_234017.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 362.32897728820336  # OPT_PARAM: {"initial": 362.32897728820336, "min": 200, "max": 500, "type": "float"}
    safety_stock = 13.245490658154692  # OPT_PARAM: {"initial": 13.245490658154692, "min": 10, "max": 60, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 1.0, "type": "float"}
    lost_sales_weight = 1.3250710607777327  # OPT_PARAM: {"initial": 1.3250710607777327, "min": 1.2, "max": 2.5, "type": "float"}

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

    # Adjust target based on pipeline concentration and lost sales cost
    pipeline_adjustment = 1.0
    if len(pipeline_orders) > 0 and sum(pipeline_orders) > 0:
        concentration = effective_pipeline / sum(pipeline_orders)
        # More aggressive adjustment given high lost sales cost (p=5 vs h=1)
        pipeline_adjustment = 0.85 + 0.3 * concentration

    # Calculate target inventory position with lost sales emphasis
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
