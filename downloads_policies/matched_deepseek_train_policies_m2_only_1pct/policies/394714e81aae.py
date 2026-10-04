# policy_hash: 394714e81aaea7678be27227ac7c3cb64f860f654aa7814be074e587627f95c5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 41
# source_prompt_files: 1
# best_target_performance: 3970.65
# best_prompt_performance: 3970.91
# best_rel_error_pct: 0.006548
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_010815.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 600.0  # OPT_PARAM: {"initial": 600.0, "min": 300, "max": 600, "type": "float"}
    safety_stock = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 30, "max": 150, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    demand_anticipation_factor = 0.976599478108178  # OPT_PARAM: {"initial": 0.976599478108178, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = base_stock + safety_stock

    # Adjust target based on pipeline status - reduce target if pipeline is full
    pipeline_total = sum(pipeline_orders)
    pipeline_adjustment = pipeline_weight * (target_inventory - pipeline_total)
    adjusted_target = target_inventory - max(0, pipeline_adjustment)

    # Calculate order needed with demand anticipation
    order_needed = adjusted_target - inventory_position
    order_needed = order_needed * demand_anticipation_factor

    # Smooth ordering to avoid large fluctuations
    smoothed_order = smoothing_factor * order_needed

    # Ensure non-negative order
    order_amount = max(0, smoothed_order)

    # Round to nearest integer for practical ordering
    return order_amount
