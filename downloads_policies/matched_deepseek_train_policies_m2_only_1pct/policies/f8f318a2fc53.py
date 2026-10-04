# policy_hash: f8f318a2fc53fc254998f9bf45f3114987d51f78ac49c9fe6e7d05a6efb36484
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 32
# source_prompt_files: 1
# best_target_performance: 11133.82
# best_prompt_performance: 11133.06
# best_rel_error_pct: 0.006826
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_062732.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 499.95744933611  # OPT_PARAM: {"initial": 499.95744933611, "min": 400, "max": 600, "type": "float"}
    safety_stock = 110.87980334146468  # OPT_PARAM: {"initial": 110.87980334146468, "min": 60, "max": 140, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    demand_anticipation = 1.3  # OPT_PARAM: {"initial": 1.3, "min": 1.0, "max": 1.3, "type": "float"}

    # Calculate inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate order-up-to level
    order_up_to = base_stock * demand_anticipation + safety_stock

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing
    order_amount = raw_order * smoothing_factor

    # Round to nearest integer and ensure non-negative
    order_amount = max(0, int(round(order_amount)))

    return order_amount
