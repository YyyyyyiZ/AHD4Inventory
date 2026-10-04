# policy_hash: 2596589bfe64042a3ca346f10a19b797ca7ddc18c834286aaebb71f9381a86d2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 6293.5
# best_prompt_performance: 6294.26
# best_rel_error_pct: 0.012076
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_052651.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 357.685775281761  # OPT_PARAM: {"initial": 357.685775281761, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 51.06922323816649  # OPT_PARAM: {"initial": 51.06922323816649, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 0.4637454808574718  # OPT_PARAM: {"initial": 0.4637454808574718, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on pipeline variability
    pipeline_std = max(0.1, sum((q - sum(pipeline_orders)/len(pipeline_orders))**2 for q in pipeline_orders)**0.5) if len(pipeline_orders) > 1 else 0
    adjusted_base = base_stock + safety_stock * min(1.0, pipeline_std / 100.0)

    # Calculate order amount with smoothing
    target = max(0, adjusted_base - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    if target > 0:
        # Smooth ordering when inventory position is close to target
        smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
        order_amount = max(0, smoothing_factor * target)
    else:
        order_amount = 0

    return order_amount
