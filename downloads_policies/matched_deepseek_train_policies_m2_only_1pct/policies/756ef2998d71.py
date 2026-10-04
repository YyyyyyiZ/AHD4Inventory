# policy_hash: 756ef2998d711d6cebbb51288d8e3d195eb3fc13b04d3195d13aa3a1b8b18ce2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 11022.86
# best_prompt_performance: 11022.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_090452.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 549.6215470504135  # OPT_PARAM: {"initial": 549.6215470504135, "min": 400, "max": 700, "type": "float"}
    pipeline_weight = 0.8557270553362482  # OPT_PARAM: {"initial": 0.8557270553362482, "min": 0.8, "max": 1.0, "type": "float"}
    smoothing_factor = 0.26019176611032085  # OPT_PARAM: {"initial": 0.26019176611032085, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock = 79.61901238213952  # OPT_PARAM: {"initial": 79.61901238213952, "min": 30, "max": 150, "type": "float"}
    demand_buffer = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.9, "max": 1.5, "type": "float"}

    # Calculate inventory position with full pipeline consideration
    inventory_position = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Base order from inventory position
    base_order = max(0, base_stock - inventory_position)

    # Add safety stock adjustment
    adjusted_order = base_order + safety_stock

    # Apply smoothing to reduce order volatility
    order_amount = smoothing_factor * adjusted_order

    return order_amount
