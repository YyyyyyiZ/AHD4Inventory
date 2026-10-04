# policy_hash: 62e95ca745daaf048ac7d967b6170558ea8aeb010584439ff27b119e35dd6109
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 27
# source_prompt_files: 1
# best_target_performance: 795.44
# best_prompt_performance: 795.47
# best_rel_error_pct: 0.003771
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_233827.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 363.0498238119669  # OPT_PARAM: {"initial": 363.0498238119669, "min": 300, "max": 600, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 50, "max": 150, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    lead_time_demand_buffer = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate lead time demand using pipeline orders
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        lead_time_demand_estimate = avg_pipeline * lead_time_demand_buffer
    else:
        lead_time_demand_estimate = 0

    # Dynamic base stock adjustment based on pipeline variability
    if len(pipeline_orders) >= 2:
        pipeline_variance = max(1, sum((q - avg_pipeline) ** 2 for q in pipeline_orders) / len(pipeline_orders))
        variability_factor = min(1.5, 1 + (pipeline_variance ** 0.5) / 100)
        adjusted_base_stock = base_stock * variability_factor
    else:
        adjusted_base_stock = base_stock

    # Calculate target inventory position
    target_position = adjusted_base_stock + safety_stock + lead_time_demand_estimate

    # Calculate order quantity with smoother adjustment
    order_needed = max(0, target_position - inventory_position)

    # Apply adjustment factor with ceiling to avoid tiny orders
    order_amount = max(0, adjustment_factor * order_needed)

    # Round to nearest integer (realistic ordering)
    return order_amount
