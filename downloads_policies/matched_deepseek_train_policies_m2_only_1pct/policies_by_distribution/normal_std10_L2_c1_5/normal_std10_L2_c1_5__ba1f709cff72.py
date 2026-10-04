# policy_hash: ba1f709cff726578c744ba2f623070f89bf13ff3bf17de6357451f768480bd06
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1244.02
# best_prompt_performance: 1237.24
# best_rel_error_pct: 0.545007
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_094705.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 401.17561205542097  # OPT_PARAM: {"initial": 401.17561205542097, "min": 300, "max": 450, "type": "float"}
    pipeline_weight = 0.7819616719515421  # OPT_PARAM: {"initial": 0.7819616719515421, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.38858713199800915  # OPT_PARAM: {"initial": 0.38858713199800915, "min": 0.1, "max": 0.5, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 10, "type": "int"}
    safety_stock = 36.365976103049306  # OPT_PARAM: {"initial": 36.365976103049306, "min": 10, "max": 50, "type": "float"}

    # Calculate effective inventory position with full pipeline consideration
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjusted base stock with safety stock
    adjusted_base = base_stock + safety_stock

    # Base stock policy with smoothing
    raw_order = adjusted_base - inventory_position
    order_amount = max(min_order, raw_order)

    # Apply exponential smoothing to reduce order volatility
    if order_amount > 0:
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * min_order
        order_amount = max(min_order, smoothed_order)

    return order_amount
