# policy_hash: 0441771903fa26a2ed72448b38c8c84b6322562a05c3aa52c70cd07bdfb202ad
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 781.1
# best_prompt_performance: 781.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_103633.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 335.4108188592845  # OPT_PARAM: {"initial": 335.4108188592845, "min": 280, "max": 380, "type": "float"}
    safety_stock = 33.97835304465499  # OPT_PARAM: {"initial": 33.97835304465499, "min": 15, "max": 40, "type": "float"}
    demand_adjustment = 0.75  # OPT_PARAM: {"initial": 0.75, "min": 0.75, "max": 0.95, "type": "float"}
    smoothing_factor = 0.2302388426776683  # OPT_PARAM: {"initial": 0.2302388426776683, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Simple demand estimate using recent pipeline arrivals
    if len(pipeline_orders) >= 2:
        recent_demand_estimate = (pipeline_orders[0] + pipeline_orders[1]) / 2 * demand_adjustment
    else:
        recent_demand_estimate = 100.0 * demand_adjustment

    # Target inventory position
    target_inventory = base_stock + safety_stock - recent_demand_estimate

    # Calculate order needed to reach target
    order_needed = max(0, target_inventory - net_inventory)

    # Apply smoothing to avoid large order swings
    smoothed_order = order_needed * smoothing_factor + pipeline_orders[-1] * (1 - smoothing_factor)

    # Round to integer
    order_amount = int(round(smoothed_order))

    return order_amount
