# policy_hash: 1baa1f6f16256314f56cf6f0310d72e5b5d206d3a5310c5a161069665f69fd49
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 2558.42
# best_prompt_performance: 2555.15
# best_rel_error_pct: 0.127813
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_055857.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 826.984339066403  # OPT_PARAM: {"initial": 826.984339066403, "min": 600, "max": 900, "type": "float"}
    safety_stock = 148.22460384379505  # OPT_PARAM: {"initial": 148.22460384379505, "min": 80, "max": 180, "type": "float"}
    smoothing_factor = 0.19214791837583356  # OPT_PARAM: {"initial": 0.19214791837583356, "min": 0.1, "max": 0.8, "type": "float"}
    min_order_threshold = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 30, "type": "float"}
    forecast_window = 4  # OPT_PARAM: {"initial": 4, "min": 2, "max": 8, "type": "int"}
    forecast_factor = 1.0301630593506326  # OPT_PARAM: {"initial": 1.0301630593506326, "min": 0.3, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use recent pipeline arrivals as demand proxy for forecasting
    recent_arrivals = pipeline_orders[:forecast_window] if len(pipeline_orders) >= forecast_window else pipeline_orders
    if recent_arrivals:
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
        forecast_adjustment = avg_recent_demand * forecast_factor
    else:
        forecast_adjustment = 0

    # Dynamic target inventory
    target_inventory = base_stock + safety_stock + forecast_adjustment

    # Calculate order needed
    order_needed = target_inventory - inventory_position

    # Apply smoothing with threshold
    if order_needed > min_order_threshold:
        order_amount = smoothing_factor * order_needed
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
