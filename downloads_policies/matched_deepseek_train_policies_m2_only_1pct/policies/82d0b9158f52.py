# policy_hash: 82d0b9158f526d7d098ef444f0844c4f01ccefc32b1e667f069b63c265164f27
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 6116.54
# best_prompt_performance: 6116.54
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_093447.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 460.9045842387487  # OPT_PARAM: {"initial": 460.9045842387487, "min": 400, "max": 600, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    safety_stock = 55.90332204223894  # OPT_PARAM: {"initial": 55.90332204223894, "min": 50, "max": 120, "type": "float"}
    min_order_threshold = 10.1  # OPT_PARAM: {"initial": 10.1, "min": 5, "max": 25, "type": "float"}
    pipeline_discount = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.8, "max": 1.0, "type": "float"}

    # Calculate weighted pipeline with discount for distant orders
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_discount ** i
        weighted_pipeline += order * weight

    effective_pipeline = weighted_pipeline * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic safety stock adjustment based on pipeline variability
    if len(pipeline_orders) > 1:
        pipeline_mean = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_var = sum((x - pipeline_mean) ** 2 for x in pipeline_orders) / len(pipeline_orders)
        adjusted_safety = safety_stock * (1 + min(0.5, pipeline_var / 10000))
    else:
        adjusted_safety = safety_stock

    target_inventory = base_stock + adjusted_safety

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with minimum order threshold
    if raw_order > min_order_threshold:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
