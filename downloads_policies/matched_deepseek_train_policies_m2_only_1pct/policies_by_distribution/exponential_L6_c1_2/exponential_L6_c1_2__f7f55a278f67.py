# policy_hash: f7f55a278f679f59532f64494c5d8978dce6579f5c1fe9fd68b81e82fc61eaeb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 29
# source_prompt_files: 2
# best_target_performance: 6002.04
# best_prompt_performance: 6002.04
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_054933.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 302.1534953204794  # OPT_PARAM: {"initial": 302.1534953204794, "min": 200, "max": 500, "type": "float"}
    safety_stock = 62.15349532047437  # OPT_PARAM: {"initial": 62.15349532047437, "min": 20, "max": 150, "type": "float"}
    demand_forecast = 60.563389475907705  # OPT_PARAM: {"initial": 60.563389475907705, "min": 50, "max": 200, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    pipeline_sum = sum(pipeline_orders)
    effective_pipeline = pipeline_weight * pipeline_sum

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock - effective_pipeline

    # Calculate order amount with smoothing
    raw_order = max(0, target_inventory - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure integer order amount
    order_amount = int(round(smoothed_order))

    return order_amount
