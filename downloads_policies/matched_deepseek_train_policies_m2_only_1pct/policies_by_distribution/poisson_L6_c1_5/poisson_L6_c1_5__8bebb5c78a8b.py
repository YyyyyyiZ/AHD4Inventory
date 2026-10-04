# policy_hash: 8bebb5c78a8bf0b726a44065277f90da334b81735cb6cac2449f562a112f83c5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 1557.46
# best_prompt_performance: 1554.81
# best_rel_error_pct: 0.170149
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_060443.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 719.2472661827168  # OPT_PARAM: {"initial": 719.2472661827168, "min": 600, "max": 900, "type": "float"}
    safety_stock = 125.64855646903678  # OPT_PARAM: {"initial": 125.64855646903678, "min": 80, "max": 180, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    min_order_threshold = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 30, "type": "float"}
    forecast_window = 4  # OPT_PARAM: {"initial": 4, "min": 2, "max": 8, "type": "int"}
    forecast_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.3, "max": 1.2, "type": "float"}
    lost_sales_weight = 3.0  # OPT_PARAM: {"initial": 3.0, "min": 1.0, "max": 3.0, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight ** i for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Use recent pipeline arrivals as demand proxy
    recent_arrivals = pipeline_orders[:forecast_window] if len(pipeline_orders) >= forecast_window else pipeline_orders
    if recent_arrivals:
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
        forecast_adjustment = avg_recent_demand * forecast_factor
    else:
        forecast_adjustment = 0

    # Dynamic target inventory
    target_inventory = base_stock + (safety_stock * lost_sales_weight) + forecast_adjustment

    # Calculate order needed
    order_needed = target_inventory - inventory_position

    # Apply smoothing with threshold
    if order_needed > min_order_threshold:
        order_amount = smoothing_factor * order_needed
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
