# policy_hash: 75d70d44a5be7981cc127385fb1f2dd474d727044bd1c0c6d4aa5b03f6bc3864
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 1567.7
# best_prompt_performance: 1567.7
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_061644.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 950.0  # OPT_PARAM: {"initial": 950.0, "min": 800, "max": 1200, "type": "float"}
    safety_multiplier = 0.7218325672332149  # OPT_PARAM: {"initial": 0.7218325672332149, "min": 0.5, "max": 2.5, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    demand_estimate = 87.76636543180976  # OPT_PARAM: {"initial": 87.76636543180976, "min": 80, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate safety stock based on lead time demand
    safety_stock = safety_multiplier * lead_time_demand

    # Calculate target inventory position
    target_position = lead_time_demand + safety_stock

    # Calculate base order using base-stock policy
    base_order = max(0, target_position - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = smoothing_factor * base_order

    # Add base demand to maintain flow
    flow_order = demand_estimate

    # Final order amount
    order_amount = max(0, smoothed_order + flow_order)

    # Round to nearest integer (as required by problem statement)
    return order_amount
