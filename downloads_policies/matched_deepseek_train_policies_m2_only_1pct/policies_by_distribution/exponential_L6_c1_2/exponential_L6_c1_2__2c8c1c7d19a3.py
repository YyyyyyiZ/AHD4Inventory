# policy_hash: 2c8c1c7d19a3a7d63a91e7b0d057888ac2e59385447f00584311d3659f86314c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 28
# source_prompt_files: 1
# best_target_performance: 6326.72
# best_prompt_performance: 6326.72
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_013157.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 285.0  # OPT_PARAM: {"initial": 285.0, "min": 100, "max": 500, "type": "float"}
    safety_stock = 75.0  # OPT_PARAM: {"initial": 75.0, "min": 20, "max": 150, "type": "float"}
    demand_estimate = 96.93777605935969  # OPT_PARAM: {"initial": 96.93777605935969, "min": 50, "max": 200, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    adjustment_smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate effective pipeline (weighted sum)
    effective_pipeline = sum(p * pipeline_weight for p in pipeline_orders)

    # Calculate target inventory level
    target_level = max(base_stock, lead_time_demand + safety_stock - effective_pipeline)

    # Calculate order amount with smoothing
    raw_order = target_level - inventory_position
    order_amount = raw_order * adjustment_smoothing

    # Ensure non-negative and round to integer
    order_amount = max(0, order_amount)
    order_amount = int(round(order_amount))

    return order_amount
