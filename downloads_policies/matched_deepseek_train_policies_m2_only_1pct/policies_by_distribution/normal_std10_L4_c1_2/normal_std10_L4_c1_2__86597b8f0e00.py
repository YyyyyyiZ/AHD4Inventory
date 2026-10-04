# policy_hash: 86597b8f0e00aa0516430b6dddff2a9d11dad1889fd78bf68e48a0623aa5f14a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 762.2
# best_prompt_performance: 762.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_102422.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 624.7785551838498  # OPT_PARAM: {"initial": 624.7785551838498, "min": 600, "max": 750, "type": "float"}
    safety_stock = 77.40708948648887  # OPT_PARAM: {"initial": 77.40708948648887, "min": 70, "max": 110, "type": "float"}
    smoothing_factor = 0.15  # OPT_PARAM: {"initial": 0.15, "min": 0.15, "max": 0.35, "type": "float"}
    pipeline_weight = 0.2613422313801415  # OPT_PARAM: {"initial": 0.2613422313801415, "min": 0.25, "max": 0.5, "type": "float"}
    imminent_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}
    demand_buffer = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.2, "type": "float"}
    lost_sales_penalty = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.3, "type": "float"}
    holding_penalty = 0.746585633915838  # OPT_PARAM: {"initial": 0.746585633915838, "min": 0.7, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjusted base stock with demand buffer
    adjusted_base_stock = base_stock * demand_buffer

    # Base order with smoothing
    desired_order = max(0, adjusted_base_stock - inventory_position)
    smoothed_order = smoothing_factor * desired_order

    # Balance holding vs lost sales costs
    if on_hand_inventory < safety_stock * 0.5:
        smoothed_order *= lost_sales_penalty
    elif on_hand_inventory > safety_stock * 2.0:
        smoothed_order *= holding_penalty

    # Dynamic safety stock adjustment based on imminent arrivals
    if pipeline_orders[0] > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        if avg_pipeline > 0:
            ratio = pipeline_orders[0] / avg_pipeline
            safety_multiplier = max(0.5, 1.5 - ratio * imminent_weight)
            safety_adjustment = safety_stock * safety_multiplier * (1.0 - pipeline_weight)
            smoothed_order += safety_adjustment

    # Pipeline coverage adjustment
    if len(pipeline_orders) > 1:
        near_term = sum(pipeline_orders[:2])
        total_pipeline = sum(pipeline_orders)
        if total_pipeline > 0:
            coverage_ratio = near_term / total_pipeline
            pipeline_adjustment = pipeline_weight * safety_stock * (1.1 - coverage_ratio)
            smoothed_order += pipeline_adjustment

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
