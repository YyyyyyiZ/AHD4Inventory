# policy_hash: 92ef7d7eab152d60bf984d7e03ae8eb9ff4515eff118825235bd05b9837d3042
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1411.8
# best_prompt_performance: 1413.99
# best_rel_error_pct: 0.155121
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_022355.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 549.8487196115017  # OPT_PARAM: {"initial": 549.8487196115017, "min": 400, "max": 800, "type": "float"}
    safety_stock = 119.48615588819209  # OPT_PARAM: {"initial": 119.48615588819209, "min": 20, "max": 150, "type": "float"}
    demand_estimate = 96.86505543868489  # OPT_PARAM: {"initial": 96.86505543868489, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with smoothing
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate base order amount
    base_order = max(0, target_position - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = smoothing_factor * base_order + (1 - smoothing_factor) * demand_estimate

    # Cap the order amount to avoid excessive ordering
    max_order = base_stock - inventory_position + demand_estimate
    order_amount = min(smoothed_order, max(0, max_order))

    return order_amount
