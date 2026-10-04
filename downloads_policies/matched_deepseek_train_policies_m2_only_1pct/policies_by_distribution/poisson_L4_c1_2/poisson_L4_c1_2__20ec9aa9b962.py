# policy_hash: 20ec9aa9b96208f6bab405edd2b706f1f2c634932ca43f169f17aec1b92b1f98
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 846.82
# best_prompt_performance: 846.82
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_001209.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 508.4000000000136  # OPT_PARAM: {"initial": 508.4000000000136, "min": 450, "max": 600, "type": "float"}
    safety_stock = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 15, "max": 40, "type": "float"}
    demand_forecast = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.3, "max": 0.8, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    order_threshold = 0.0999999999995529  # OPT_PARAM: {"initial": 0.0999999999995529, "min": 0.0, "max": 0.2, "type": "float"}
    pipeline_lookback = 2  # OPT_PARAM: {"initial": 2, "min": 1, "max": 4, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate average of recent pipeline orders
    lookback = min(pipeline_lookback, len(pipeline_orders))
    recent_pipeline = sum(pipeline_orders[-lookback:]) / lookback if lookback > 0 else 0

    # Pipeline adjustment based on recent orders
    pipeline_adjustment = pipeline_weight * recent_pipeline

    # Target inventory level
    target_inventory = base_stock + safety_stock - pipeline_adjustment

    # Order-up-to quantity
    order_needed = target_inventory - inventory_position

    # Apply smoothing with threshold
    if order_needed > demand_forecast * order_threshold:
        smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
