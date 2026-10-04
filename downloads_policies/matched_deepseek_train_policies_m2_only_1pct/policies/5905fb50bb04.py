# policy_hash: 5905fb50bb040332ef071c2f676c1cb0b8377e5dad70a959fecc5388d7124d62
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 778.64
# best_prompt_performance: 778.64
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_185225.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 374.6548483069121  # OPT_PARAM: {"initial": 374.6548483069121, "min": 300, "max": 450, "type": "float"}
    safety_stock = 85.00630510892371  # OPT_PARAM: {"initial": 85.00630510892371, "min": 60, "max": 120, "type": "float"}
    demand_estimate = 94.32928829262043  # OPT_PARAM: {"initial": 94.32928829262043, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight**(len(pipeline_orders)-i-1)
                          for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected lead time demand
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Dynamic safety stock based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    if pipeline_sum > 0:
        pipeline_std = (sum((p - pipeline_sum/len(pipeline_orders))**2
                          for p in pipeline_orders) / len(pipeline_orders))**0.5
        adjusted_safety = safety_stock * (1 + 0.3 * pipeline_std / demand_estimate)
    else:
        adjusted_safety = safety_stock

    # Target inventory position
    target_position = expected_lead_time_demand + adjusted_safety

    # Order calculation with base stock constraint
    raw_order = max(0, target_position - inventory_position)
    base_stock_order = max(0, base_stock - inventory_position)

    # Use the smaller of the two approaches
    order_amount = min(raw_order, base_stock_order)

    # Smooth with demand estimate
    order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Ensure non-negative integer
    order_amount = max(0, int(round(order_amount)))

    return order_amount
