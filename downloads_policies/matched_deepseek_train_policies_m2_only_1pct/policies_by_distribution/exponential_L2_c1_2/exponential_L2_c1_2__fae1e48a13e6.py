# policy_hash: fae1e48a13e611ed7cda294327741990129f19575b5e6cd0f9676c4a9a35b979
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 5893.96
# best_prompt_performance: 5893.96
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_030352.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 181.00000000024434  # OPT_PARAM: {"initial": 181.00000000024434, "min": 150, "max": 350, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 20, "max": 100, "type": "float"}
    demand_estimate = 70.0  # OPT_PARAM: {"initial": 70.0, "min": 70, "max": 130, "type": "float"}
    smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.3, "type": "float"}

    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory position
    target_position = base_stock + safety_stock

    # Calculate raw order quantity
    raw_order = max(0, target_position - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = smoothing * raw_order + (1 - smoothing) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
