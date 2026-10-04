# policy_hash: 86e0909334ebe22019e7d898c55d2bc0b9c25dc19e1a3d1921ad86bb0b17deed
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1294.3
# best_prompt_performance: 1294.3
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_004426.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 461.1808358371439  # OPT_PARAM: {"initial": 461.1808358371439, "min": 400, "max": 550, "type": "float"}
    safety_stock = 20.315503204522226  # OPT_PARAM: {"initial": 20.315503204522226, "min": 10, "max": 50, "type": "float"}
    demand_forecast = 96.81004999107688  # OPT_PARAM: {"initial": 96.81004999107688, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.1, "type": "float"}

    # Calculate total pipeline (simple sum, no weighting)
    total_pipeline = sum(pipeline_orders)
    inventory_position = on_hand_inventory + total_pipeline

    # Standard order-up-to policy
    order_up_to = base_stock + safety_stock

    # Order-up-to with smoothing
    raw_order = max(0, order_up_to - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
