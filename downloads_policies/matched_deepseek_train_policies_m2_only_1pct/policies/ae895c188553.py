# policy_hash: ae895c1885535b33982dc25da0a2e8e986de7845f7535450f6f08d001c129f93
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 5900.56
# best_prompt_performance: 5900.56
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_024823.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 138.28461160019032  # OPT_PARAM: {"initial": 138.28461160019032, "min": 100, "max": 400, "type": "float"}
    safety_stock = 19.729430523698884  # OPT_PARAM: {"initial": 19.729430523698884, "min": 10, "max": 150, "type": "float"}
    smoothing = 0.46340634670009734  # OPT_PARAM: {"initial": 0.46340634670009734, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected lead time demand (L=2 periods)
    # Using historical average demand from trajectories
    avg_demand_per_period = 100.0
    lead_time_demand_estimate = avg_demand_per_period * len(pipeline_orders)

    # Calculate target inventory position
    target_inventory_position = base_stock + safety_stock

    # Calculate raw order quantity
    raw_order = max(0, target_inventory_position - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = smoothing * raw_order + (1 - smoothing) * avg_demand_per_period

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
