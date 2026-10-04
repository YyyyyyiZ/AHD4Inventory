# policy_hash: aaf31dc32233de0cf3e2d147114658d8dab8537a8139eeedb57a4b66c54a4f17
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 12270.96
# best_prompt_performance: 12270.42
# best_rel_error_pct: 0.004401
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_060753.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 400.0089236666995  # OPT_PARAM: {"initial": 400.0089236666995, "min": 400, "max": 700, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.7, "type": "float"}
    demand_buffer = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 2.5, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate average pipeline demand
    avg_pipeline_demand = 0.0
    if len(pipeline_orders) > 0:
        avg_pipeline_demand = sum(pipeline_orders) / len(pipeline_orders)

    # Adjust base stock based on pipeline demand pattern
    adjustment_factor = 0.0
    if avg_pipeline_demand > 0:
        # If pipeline shows high demand, increase base stock
        adjustment_factor = min(1.5, avg_pipeline_demand / 100.0) * demand_buffer

    # Calculate order-up-to level
    order_up_to = base_stock * (1.0 + adjustment_factor)

    # Calculate raw order amount
    raw_order = max(0.0, order_up_to - inventory_position)

    # Apply smoothing to avoid large order swings
    if raw_order > 0:
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = 0.0

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
