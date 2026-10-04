# policy_hash: 412abd8270c9e84c9fbed241532b1cce08174eccfd0e73dba2f2f8df68fa3a52
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 1249.9
# best_prompt_performance: 1249.9
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_064653.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 980.0  # OPT_PARAM: {"initial": 980.0, "min": 800, "max": 1200, "type": "float"}
    safety_multiplier = 1.5240351261368732  # OPT_PARAM: {"initial": 1.5240351261368732, "min": 0.5, "max": 2.5, "type": "float"}
    smoothing_factor = 0.074812997606581  # OPT_PARAM: {"initial": 0.074812997606581, "min": 0.05, "max": 0.3, "type": "float"}
    demand_estimate = 104.70459638388894  # OPT_PARAM: {"initial": 104.70459638388894, "min": 80, "max": 120, "type": "float"}
    flow_weight = 0.7940959097436857  # OPT_PARAM: {"initial": 0.7940959097436857, "min": 0.1, "max": 1.0, "type": "float"}
    pipeline_weight = 0.7605891620844645  # OPT_PARAM: {"initial": 0.7605891620844645, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight**i for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

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
