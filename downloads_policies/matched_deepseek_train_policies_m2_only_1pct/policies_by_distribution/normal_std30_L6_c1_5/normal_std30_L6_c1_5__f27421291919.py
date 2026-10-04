# policy_hash: f274212919196bf5b03980bb354b823694a836d7af252d98d19800407e95352f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 4629.34
# best_prompt_performance: 4629.91
# best_rel_error_pct: 0.012313
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_122142.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 739.7433470593021  # OPT_PARAM: {"initial": 739.7433470593021, "min": 650, "max": 850, "type": "float"}
    safety_stock = 172.59669461976858  # OPT_PARAM: {"initial": 172.59669461976858, "min": 140, "max": 220, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.25, "type": "float"}
    pipeline_weight = 0.6229060146845867  # OPT_PARAM: {"initial": 0.6229060146845867, "min": 0.4, "max": 0.8, "type": "float"}
    lost_sales_penalty_factor = 1.3053766639112365  # OPT_PARAM: {"initial": 1.3053766639112365, "min": 1.1, "max": 1.5, "type": "float"}
    pipeline_correction = 0.8642748559276313  # OPT_PARAM: {"initial": 0.8642748559276313, "min": 0.5, "max": 1.2, "type": "float"}
    min_order_threshold = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 10.0, "max": 50.0, "type": "float"}

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
