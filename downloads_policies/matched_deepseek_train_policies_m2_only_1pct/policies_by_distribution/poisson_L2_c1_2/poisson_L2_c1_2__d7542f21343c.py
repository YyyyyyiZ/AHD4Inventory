# policy_hash: d7542f21343cdcf89d0a81e9c118be878c64739b20cdc31e920d2c2497b5aba0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 963.42
# best_prompt_performance: 963.42
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_102104.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 325.0019336209205  # OPT_PARAM: {"initial": 325.0019336209205, "min": 200, "max": 400, "type": "float"}
    safety_stock = 25.001933620920557  # OPT_PARAM: {"initial": 25.001933620920557, "min": 10, "max": 50, "type": "float"}
    demand_smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.2, "type": "float"}
    adjustment_factor = 0.7800610765367514  # OPT_PARAM: {"initial": 0.7800610765367514, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of pipeline arrivals
    # More weight on recent arrivals
    if len(pipeline_orders) >= 2:
        # Weighted average: recent arrivals have higher weight
        weights = [0.6, 0.4]  # Fixed weights for two most recent arrivals
        recent_demand_estimate = (pipeline_orders[0] * weights[0] +
                                 pipeline_orders[1] * weights[1]) * demand_smoothing
    else:
        recent_demand_estimate = 100.0 * demand_smoothing

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock - recent_demand_estimate

    # Calculate order amount with partial adjustment
    raw_order = max(0, target_inventory - net_inventory)
    order_amount = int(round(raw_order * adjustment_factor))

    return order_amount
