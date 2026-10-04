# policy_hash: fa6e0b911ba2fd9b8352314be1febd9e1f578d78ee06482da89fb62fa5bd568e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 4412.22
# best_prompt_performance: 4414.66
# best_rel_error_pct: 0.055301
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_230649.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 471.7725003271094  # OPT_PARAM: {"initial": 471.7725003271094, "min": 100, "max": 800, "type": "float"}
    safety_stock = 101.77250032711524  # OPT_PARAM: {"initial": 101.77250032711524, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.3493293812851099  # OPT_PARAM: {"initial": 0.3493293812851099, "min": 0.1, "max": 1.0, "type": "float"}
    demand_forecast_factor = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 0.8, "max": 1.5, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted average of recent pipeline orders
    # (pipeline orders reflect past demand, which can indicate future demand)
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[:3]  # Look at most recent 3 orders
        avg_recent = sum(recent_orders) / len(recent_orders)
        demand_estimate = demand_forecast_factor * avg_recent
    else:
        demand_estimate = 100.0  # Default estimate

    # Adjust base stock based on demand estimate and safety stock
    adjusted_base_stock = base_stock + safety_stock + pipeline_weight * demand_estimate

    # Calculate order-up-to level
    order_up_to = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to avoid large swings
    order_amount = smoothing_factor * order_up_to

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
