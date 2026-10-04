# policy_hash: b9d3a3c345bbc7c5181904cb76b5adf141cd7beaa479328a66e37884c6fea43f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 7047.4
# best_prompt_performance: 7047.4
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_092141.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 280.6712532108536  # OPT_PARAM: {"initial": 280.6712532108536, "min": 200, "max": 400, "type": "float"}
    safety_stock = 116.37202956417998  # OPT_PARAM: {"initial": 116.37202956417998, "min": 80, "max": 200, "type": "float"}
    pipeline_weight = 0.7999999999999999  # OPT_PARAM: {"initial": 0.7999999999999999, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline coverage
    # More weight to near-term arrivals
    weighted_pipeline = 0
    L = len(pipeline_orders)
    for i, order in enumerate(pipeline_orders):
        # Exponential decay weight: earliest arrivals (i=0) get highest weight
        weight = pipeline_weight ** (L - i - 1)
        weighted_pipeline += order * weight

    # Effective coverage considers weighted pipeline
    effective_coverage = on_hand_inventory + weighted_pipeline

    # Dynamic order-up-to level based on pipeline uncertainty
    # Reduce base stock when pipeline is heavily weighted (more certain)
    pipeline_uncertainty = 1.0 - (weighted_pipeline / sum(pipeline_orders) if sum(pipeline_orders) > 0 else 0)
    adjusted_base = base_stock + safety_stock * pipeline_uncertainty

    # Target inventory position
    target_position = adjusted_base

    # Order amount calculation
    raw_order = max(0, target_position - effective_coverage)

    # Smooth with traditional inventory position difference
    traditional_order = max(0, target_position - inventory_position)

    # Blend: mostly follow effective coverage, but smooth with traditional
    order_amount = raw_order * (1 - smoothing_factor) + traditional_order * smoothing_factor
    order_amount = max(0, order_amount)

    return order_amount
