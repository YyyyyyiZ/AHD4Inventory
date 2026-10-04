# policy_hash: 7f3459daeb5c089b8a3c97df3eecfccf6bb02a76ffd6a67f52c0530e59f711b0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1505.51
# best_prompt_performance: 1505.82
# best_rel_error_pct: 0.020591
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_004244.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 430.1110273124953  # OPT_PARAM: {"initial": 430.1110273124953, "min": 380, "max": 480, "type": "float"}
    safety_stock = 35.11102731249528  # OPT_PARAM: {"initial": 35.11102731249528, "min": 20, "max": 50, "type": "float"}
    demand_forecast = 100.22802134916756  # OPT_PARAM: {"initial": 100.22802134916756, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate total pipeline (unweighted)
    total_pipeline = sum(pipeline_orders)

    # Calculate inventory position (on-hand + total pipeline)
    inventory_position = on_hand_inventory + total_pipeline

    # Simple order-up-to policy
    order_up_to = base_stock + safety_stock

    # Calculate raw order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with demand forecast
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
