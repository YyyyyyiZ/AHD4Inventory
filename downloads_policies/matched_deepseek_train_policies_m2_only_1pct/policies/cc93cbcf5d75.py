# policy_hash: cc93cbcf5d751e31232e96dc2231db71b5e09bc0ec563283128ec788521cddd1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 3167.4
# best_prompt_performance: 3189.3
# best_rel_error_pct: 0.691419
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_050032.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 565.5999999999975  # OPT_PARAM: {"initial": 565.5999999999975, "min": 300, "max": 800, "type": "float"}
    safety_stock = 30.600000000001145  # OPT_PARAM: {"initial": 30.600000000001145, "min": 0, "max": 50, "type": "float"}
    smoothing_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple base-stock policy with smoothing
    target = base_stock + safety_stock

    # Calculate raw order needed
    raw_order = max(0, target - inventory_position)

    # Apply smoothing using average of recent pipeline orders
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-min(2, len(pipeline_orders)):]
        avg_recent = sum(recent_orders) / len(recent_orders)
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * avg_recent
    else:
        smoothed_order = raw_order

    # Round to nearest integer
    order_amount = int(round(max(0, smoothed_order)))

    return order_amount
