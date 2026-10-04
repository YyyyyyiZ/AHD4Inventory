# policy_hash: de85167fbc76a86a512564e8de478222ec3604e39836971cf87f6bb71532d374
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 71
# source_prompt_files: 2
# best_target_performance: 5999.24
# best_prompt_performance: 5999.24
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_053309.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 356.9601574426319  # OPT_PARAM: {"initial": 356.9601574426319, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 66.78585299496207  # OPT_PARAM: {"initial": 66.78585299496207, "min": 10, "max": 500, "type": "float"}
    smoothing_factor = 0.16912225271613346  # OPT_PARAM: {"initial": 0.16912225271613346, "min": 0.01, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    avg_pipeline = pipeline_sum / len(pipeline_orders) if pipeline_orders else 0
    pipeline_variability = sum(abs(p - avg_pipeline) for p in pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0

    # Dynamic adjustment factor
    adjustment_factor = 0.2784420358392114  # OPT_PARAM: {"initial": 0.2784420358392114, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate target inventory position
    target_inventory = (base_stock * adjustment_factor) + safety_stock

    # Calculate order amount with smoothing
    raw_order = max(0, target_inventory - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure integer order amount
    order_amount = int(round(smoothed_order))

    return order_amount
