# policy_hash: 2bc92072c35c615756da91472f2a667495a05a1098c53d6a986d432285d638a3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 53
# source_prompt_files: 1
# best_target_performance: 3797.24
# best_prompt_performance: 3796.25
# best_rel_error_pct: 0.026072
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_012535.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 456.7562830896437  # OPT_PARAM: {"initial": 456.7562830896437, "min": 300, "max": 600, "type": "float"}
    safety_stock = 86.75628308963954  # OPT_PARAM: {"initial": 86.75628308963954, "min": 30, "max": 150, "type": "float"}
    smoothing_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.3, "max": 1.0, "type": "float"}
    demand_anticipation_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    lost_sales_penalty_weight = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = base_stock + safety_stock

    # Adjust target based on pipeline status - more aggressive adjustment
    pipeline_total = sum(pipeline_orders)
    pipeline_adjustment = pipeline_weight * (target_inventory - pipeline_total)
    adjusted_target = target_inventory - max(0, pipeline_adjustment)

    # Increase target when lost sales are more costly (p > h)
    cost_ratio_adjustment = lost_sales_penalty_weight * (5.0 / 1.0)  # p/h ratio
    adjusted_target = adjusted_target * (1.0 + 0.1 * (cost_ratio_adjustment - 1.0))

    # Calculate order needed with demand anticipation
    order_needed = adjusted_target - inventory_position
    order_needed = order_needed * demand_anticipation_factor

    # Smooth ordering to avoid large fluctuations
    smoothed_order = smoothing_factor * order_needed

    # Ensure non-negative order
    order_amount = max(0, smoothed_order)

    # Round to nearest integer for practical ordering
    return order_amount
