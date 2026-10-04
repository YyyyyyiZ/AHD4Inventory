# policy_hash: 269a5e310bf9129554146a25f0990fa08d613e59be583b4c3a95c3548ee88f94
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 10161.03
# best_prompt_performance: 10161.03
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_234104.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 434.7230543432346  # OPT_PARAM: {"initial": 434.7230543432346, "min": 300, "max": 600, "type": "float"}
    safety_stock = 34.72305434323126  # OPT_PARAM: {"initial": 34.72305434323126, "min": 0, "max": 150, "type": "float"}
    pipeline_weight = 0.661112104165346  # OPT_PARAM: {"initial": 0.661112104165346, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing = 0.3726873831067372  # OPT_PARAM: {"initial": 0.3726873831067372, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline (weighted sum with more weight on near-term arrivals)
    effective_pipeline = 0
    for i, q in enumerate(pipeline_orders):
        weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
        effective_pipeline += q * weight

    # Adjust target based on pipeline timing
    target = base_stock + safety_stock - (1 - pipeline_weight) * effective_pipeline

    # Calculate order needed
    order_needed = max(0, target - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    if order_needed > 0:
        order_amount = smoothing * order_needed
    else:
        order_amount = 0

    return order_amount
