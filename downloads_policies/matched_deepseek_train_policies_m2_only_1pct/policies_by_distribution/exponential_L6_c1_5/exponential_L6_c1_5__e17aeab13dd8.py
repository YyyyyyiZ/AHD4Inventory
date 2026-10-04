# policy_hash: e17aeab13dd8f69d295df4c13e0ffd9e5688945d45c3515b840c7513debf68b3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 11845.98
# best_prompt_performance: 11845.98
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_015954.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 354.17036973703506  # OPT_PARAM: {"initial": 354.17036973703506, "min": 100, "max": 800, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + weighted_pipeline

    # Simple base-stock policy
    order_amount = max(0, base_stock - inventory_position)

    # Smooth ordering using recent pipeline average
    if len(pipeline_orders) >= 2:
        avg_recent = sum(pipeline_orders[-2:]) / 2
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_recent

    # Ensure non-negative and integer
    return order_amount
