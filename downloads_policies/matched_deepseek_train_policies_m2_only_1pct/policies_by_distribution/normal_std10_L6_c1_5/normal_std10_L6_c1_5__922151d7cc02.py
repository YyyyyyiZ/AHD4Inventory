# policy_hash: 922151d7cc022b882b8740445891452b3b086ed87c9dbde037b17af4b600b92a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 83
# source_prompt_files: 1
# best_target_performance: 1249.95
# best_prompt_performance: 1249.95
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_062832.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 1050.0  # OPT_PARAM: {"initial": 1050.0, "min": 800, "max": 1200, "type": "float"}
    safety_multiplier = 1.614483585184354  # OPT_PARAM: {"initial": 1.614483585184354, "min": 0.5, "max": 2.5, "type": "float"}
    smoothing_factor = 0.06271538493006533  # OPT_PARAM: {"initial": 0.06271538493006533, "min": 0.05, "max": 0.3, "type": "float"}
    demand_estimate = 108.03237488898708  # OPT_PARAM: {"initial": 108.03237488898708, "min": 80, "max": 120, "type": "float"}
    flow_weight = 0.810287733321048  # OPT_PARAM: {"initial": 0.810287733321048, "min": 0.1, "max": 1.0, "type": "float"}

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

    # Blend smoothed order with flow order
    order_amount = max(0, flow_weight * flow_order + (1 - flow_weight) * smoothed_order)

    # Round to nearest integer (as required by problem statement)
    return order_amount
