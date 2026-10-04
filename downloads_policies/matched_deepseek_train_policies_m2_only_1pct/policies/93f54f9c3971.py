# policy_hash: 93f54f9c39716bf59c9d21eb7ce6f0665404039ac757be750511a977838237ef
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 6791.25
# best_prompt_performance: 6791.06
# best_rel_error_pct: 0.002798
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_035031.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 175.43418956142608  # OPT_PARAM: {"initial": 175.43418956142608, "min": 50, "max": 400, "type": "float"}
    safety_stock = 41.914586011193435  # OPT_PARAM: {"initial": 41.914586011193435, "min": 10, "max": 150, "type": "float"}
    demand_smoothing = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.5, "type": "float"}
    pipeline_coverage = 0.5739184777271088  # OPT_PARAM: {"initial": 0.5739184777271088, "min": 0.5, "max": 1.2, "type": "float"}
    reorder_point = 60.3  # OPT_PARAM: {"initial": 60.3, "min": 20, "max": 200, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand from pipeline (orders placed are responses to past demand)
    # Use weighted average of pipeline orders as demand indicator
    if pipeline_orders:
        # Give more weight to recent orders
        weights = [0.3, 0.25, 0.2, 0.15, 0.1][:len(pipeline_orders)]
        weighted_sum = sum(w * o for w, o in zip(weights, pipeline_orders))
        estimated_demand = weighted_sum / sum(weights[:len(pipeline_orders)])
    else:
        estimated_demand = 0

    # Smooth demand estimate
    smoothed_demand = demand_smoothing * estimated_demand + (1 - demand_smoothing) * (base_stock / 4)

    # Calculate pipeline coverage needed
    pipeline_needed = pipeline_coverage * smoothed_demand * len(pipeline_orders)

    # Dynamic base stock adjustment
    dynamic_base = base_stock + safety_stock + pipeline_needed

    # Calculate order amount
    if inventory_position < reorder_point:
        # Below reorder point: order up to dynamic base
        order_amount = max(0, dynamic_base - inventory_position)
    else:
        # Above reorder point: order only if significantly below target
        order_amount = max(0, 0.7 * (dynamic_base - inventory_position))

    # Round to integer
    return order_amount
