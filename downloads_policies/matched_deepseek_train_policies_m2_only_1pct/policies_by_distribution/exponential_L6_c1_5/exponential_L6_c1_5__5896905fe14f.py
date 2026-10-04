# policy_hash: 5896905fe14f4a9a46bbeb9198b88de71cd446e150f13274815660f339352b18
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 11345.38
# best_prompt_performance: 11345.02
# best_rel_error_pct: 0.003173
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_050615.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 424.68941068355326  # OPT_PARAM: {"initial": 424.68941068355326, "min": 300, "max": 700, "type": "float"}
    safety_stock = 180.0  # OPT_PARAM: {"initial": 180.0, "min": 100, "max": 300, "type": "float"}
    demand_estimate = 60.00000000000351  # OPT_PARAM: {"initial": 60.00000000000351, "min": 60, "max": 150, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    min_order_threshold = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Dynamic safety stock based on pipeline variability
    pipeline_mean = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    pipeline_variance = sum((p - pipeline_mean) ** 2 for p in pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    dynamic_safety = safety_stock * (1 + 0.05 * pipeline_variance / (demand_estimate ** 2 + 1))

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + dynamic_safety

    # Use the minimum of base_stock and dynamic target for better balance
    order_up_to = min(base_stock, target_inventory)

    # Calculate order amount with smoothing
    raw_order = max(0, order_up_to - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_estimate

    # Apply minimum order threshold
    if smoothed_order < demand_estimate * min_order_threshold:
        smoothed_order = 0

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
