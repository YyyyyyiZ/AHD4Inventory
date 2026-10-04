# policy_hash: 2ec4ca8da247dfb640fa3ccd69457b7c1692ed5cbcc4a1e9e7b50687428068f1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 1226.74
# best_prompt_performance: 1226.74
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_005519.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 461.8648155921706  # OPT_PARAM: {"initial": 461.8648155921706, "min": 400, "max": 550, "type": "float"}
    safety_stock = 20.310947182040888  # OPT_PARAM: {"initial": 20.310947182040888, "min": 10, "max": 50, "type": "float"}
    demand_forecast = 96.8056113021022  # OPT_PARAM: {"initial": 96.8056113021022, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.1, "type": "float"}

    # Calculate total pipeline inventory
    total_pipeline = sum(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + total_pipeline

    # Calculate order-up-to level
    order_up_to = base_stock + safety_stock

    # Calculate gap to order-up-to level
    gap = order_up_to - inventory_position

    # Apply smoothing to order quantity
    if gap > 0:
        raw_order = gap
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
        order_amount = max(0, int(round(smoothed_order)))
    else:
        order_amount = 0

    return order_amount
