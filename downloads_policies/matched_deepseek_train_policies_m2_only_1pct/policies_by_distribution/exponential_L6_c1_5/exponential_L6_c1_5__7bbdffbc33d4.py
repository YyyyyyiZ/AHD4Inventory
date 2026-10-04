# policy_hash: 7bbdffbc33d4bdf6769bbc707bb55aa1a584957411218f2edf42aefab1e5264a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 39
# source_prompt_files: 1
# best_target_performance: 11200.19
# best_prompt_performance: 11200.19
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_063520.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 315.90302835295125  # OPT_PARAM: {"initial": 315.90302835295125, "min": 200, "max": 400, "type": "float"}
    safety_factor = 2.1826439617542897  # OPT_PARAM: {"initial": 2.1826439617542897, "min": 1.2, "max": 2.5, "type": "float"}
    pipeline_coverage = 0.9606539247459366  # OPT_PARAM: {"initial": 0.9606539247459366, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing = 0.10187943796638825  # OPT_PARAM: {"initial": 0.10187943796638825, "min": 0.05, "max": 0.3, "type": "float"}
    lost_sales_weight = 1.308468997941226  # OPT_PARAM: {"initial": 1.308468997941226, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    # Weight orders by their arrival proximity
    L = len(pipeline_orders)
    effective_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        # Exponential decay weight: orders arriving sooner get higher weight
        weight = 0.8044305869763629  # OPT_PARAM: {"initial": 0.8044305869763629, "min": 0.5, "max": 0.9, "type": "float"}
        effective_pipeline += order * weight

    # Dynamic safety stock adjustment based on pipeline variability
    if L > 1:
        pipeline_std = (max(pipeline_orders) - min(pipeline_orders)) / 2 if max(pipeline_orders) > 0 else 0
        dynamic_safety = safety_factor * (1 + pipeline_std / (base_stock + 1))
    else:
        dynamic_safety = safety_factor

    # Target inventory position with lost-sales emphasis
    target_inventory = base_stock * dynamic_safety * lost_sales_weight

    # Order calculation: account for effective pipeline coverage
    net_order = target_inventory - (inventory_position - pipeline_coverage * effective_pipeline)

    # Apply smoothing and ensure non-negative
    if net_order > 0:
        order_amount = net_order * smoothing
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
