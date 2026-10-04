# policy_hash: 59ef8d82f28d924aa918e5529e5dd8b7d128beccc8cabfc98606dff0337a94c4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 11708.81
# best_prompt_performance: 11708.56
# best_rel_error_pct: 0.002135
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_061224.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 562.517578915484  # OPT_PARAM: {"initial": 562.517578915484, "min": 200, "max": 600, "type": "float"}
    safety_stock = 300.0  # OPT_PARAM: {"initial": 300.0, "min": 50, "max": 300, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing = 0.29465314501292594  # OPT_PARAM: {"initial": 0.29465314501292594, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust target based on pipeline coverage
    pipeline_total = sum(pipeline_orders)
    adjusted_target = base_stock + safety_stock - pipeline_weight * pipeline_total

    # Calculate raw order
    raw_order = max(0, adjusted_target - inventory_position)

    # Apply smoothing only for moderate adjustments
    if raw_order > 0:
        order_amount = raw_order * smoothing
    else:
        order_amount = 0

    return order_amount
