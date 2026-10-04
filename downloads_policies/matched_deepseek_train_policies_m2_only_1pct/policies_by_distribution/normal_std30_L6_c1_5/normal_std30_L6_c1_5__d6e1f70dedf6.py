# policy_hash: d6e1f70dedf62ffc9b29245f0f8d39a9a722d6154de6aa278b702675238f3437
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 4621.94
# best_prompt_performance: 4618.42
# best_rel_error_pct: 0.076158
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_123033.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 727.1450596886112  # OPT_PARAM: {"initial": 727.1450596886112, "min": 650, "max": 850, "type": "float"}
    safety_stock = 188.35462370275098  # OPT_PARAM: {"initial": 188.35462370275098, "min": 140, "max": 220, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.25, "type": "float"}
    pipeline_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.8, "type": "float"}
    lost_sales_penalty_factor = 1.2000000000000002  # OPT_PARAM: {"initial": 1.2000000000000002, "min": 1.1, "max": 1.5, "type": "float"}
    pipeline_correction = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    min_order_threshold = 25.359374042711696  # OPT_PARAM: {"initial": 25.359374042711696, "min": 10.0, "max": 50.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline with stronger emphasis on near-term arrivals
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Adjust base stock based on pipeline coverage
    pipeline_coverage = weighted_pipeline / (base_stock + 1e-6)
    adjusted_base = base_stock * (1 + demand_forecast_factor * (1 - pipeline_coverage * pipeline_correction))

    # Calculate desired order-up-to level with enhanced lost sales protection
    desired_level = adjusted_base + safety_stock * lost_sales_penalty_factor

    # Calculate order amount with smoothing and minimum order threshold
    raw_order = desired_level - inventory_position
    smoothed_order = smoothing_factor * raw_order

    # Apply minimum order threshold to avoid tiny orders
    if smoothed_order > 0 and smoothed_order < min_order_threshold:
        order_amount = min_order_threshold
    else:
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    return order_amount
