# policy_hash: 222e111bcc63cb2ee31b8a3b57ad974c68a74650d023854f571aa97f19d9d877
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 6238.12
# best_prompt_performance: 6237.1
# best_rel_error_pct: 0.016351
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_091342.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on pipeline variability
    pipeline_std = max(1.0, sum((q - effective_pipeline/len(pipeline_orders))**2 for q in pipeline_orders)**0.5)
    adjustment_factor = 50.00000000004368  # OPT_PARAM: {"initial": 50.00000000004368, "min": 50, "max": 300, "type": "float"}

    adjusted_base_stock = base_stock * adjustment_factor + safety_stock

    # Calculate order amount with smoothing
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Smooth ordering to avoid large fluctuations
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    if raw_order > 0:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
