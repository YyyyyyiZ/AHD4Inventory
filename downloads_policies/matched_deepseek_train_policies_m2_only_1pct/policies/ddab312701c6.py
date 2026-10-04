# policy_hash: ddab312701c6938061359fff5b87329f906ba450b93d4ec74fbff93480ff9e3d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 2695.41
# best_prompt_performance: 2696.14
# best_rel_error_pct: 0.027083
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_065756.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 750.0  # OPT_PARAM: {"initial": 750.0, "min": 600, "max": 900, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 50, "max": 150, "type": "float"}
    pipeline_weight = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.7, "max": 1.0, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic order-up-to level based on pipeline composition
    # Give more weight to imminent arrivals
    weighted_pipeline_sum = 0
    for i, order in enumerate(pipeline_orders):
        weight = 1.0 - (i * 0.15)  # OPT_PARAM: {"initial": 0.15, "min": 0.05, "max": 0.25, "type": "float"}
        weighted_pipeline_sum += order * weight

    # Adjust base stock based on pipeline timing
    pipeline_timing_factor = 1.0 + (weighted_pipeline_sum / (base_stock + 1)) * 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.4, "type": "float"}
    adjusted_base_stock = base_stock * pipeline_timing_factor

    # Calculate order-up-to level
    order_up_to = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply non-linear smoothing
    if order_amount > 0:
        smoothing_exponent = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.5, "max": 1.0, "type": "float"}
        order_amount = order_amount ** smoothing_exponent

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
