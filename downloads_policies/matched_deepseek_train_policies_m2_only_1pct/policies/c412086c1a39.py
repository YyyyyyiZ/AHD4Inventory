# policy_hash: c412086c1a393ad3ef48b532ce5f6bc2c95e2bc1381fda04d0a5611e6c407057
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 769.68
# best_prompt_performance: 769.68
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_101736.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 627.7977795886296  # OPT_PARAM: {"initial": 627.7977795886296, "min": 550, "max": 700, "type": "float"}
    safety_stock = 77.15862962002815  # OPT_PARAM: {"initial": 77.15862962002815, "min": 70, "max": 110, "type": "float"}
    smoothing_factor = 0.15  # OPT_PARAM: {"initial": 0.15, "min": 0.15, "max": 0.35, "type": "float"}
    pipeline_weight = 0.25  # OPT_PARAM: {"initial": 0.25, "min": 0.25, "max": 0.5, "type": "float"}
    imminent_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}
    demand_buffer = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.2, "type": "float"}
    lost_sales_penalty = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjusted base stock with demand buffer
    adjusted_base_stock = base_stock * demand_buffer

    # Base order with smoothing
    desired_order = max(0, adjusted_base_stock - inventory_position)
    smoothed_order = smoothing_factor * desired_order

    # Lost sales penalty adjustment
    if on_hand_inventory < safety_stock * 0.5:
        smoothed_order *= lost_sales_penalty

    # Dynamic safety stock adjustment based on imminent arrivals
    if pipeline_orders[0] > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        if avg_pipeline > 0:
            ratio = pipeline_orders[0] / avg_pipeline
            # Simplified adjustment
            safety_multiplier = max(0.5, 1.5 - ratio * imminent_weight)
            safety_adjustment = safety_stock * safety_multiplier * (1.0 - pipeline_weight)
            smoothed_order += safety_adjustment

    # Pipeline coverage adjustment
    if len(pipeline_orders) > 1:
        near_term = sum(pipeline_orders[:2])
        total_pipeline = sum(pipeline_orders)
        if total_pipeline > 0:
            coverage_ratio = near_term / total_pipeline
            # Linear adjustment
            pipeline_adjustment = pipeline_weight * safety_stock * (1.1 - coverage_ratio)
            smoothed_order += pipeline_adjustment

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
