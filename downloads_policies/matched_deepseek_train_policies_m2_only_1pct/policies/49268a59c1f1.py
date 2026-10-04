# policy_hash: 49268a59c1f1434bf16042ac689ddae3658a6c2497e9348ec7975da77f35ccc1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 6075.3
# best_prompt_performance: 6075.3
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_092851.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 429.10907312531083  # OPT_PARAM: {"initial": 429.10907312531083, "min": 350, "max": 550, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.6, "type": "float"}
    safety_stock = 33.306899861703705  # OPT_PARAM: {"initial": 33.306899861703705, "min": 30, "max": 100, "type": "float"}
    demand_buffer = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate effective pipeline with weighted sum
    effective_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on recent pipeline variability
    recent_orders = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
    if recent_orders:
        avg_recent = sum(recent_orders) / len(recent_orders)
        variability_factor = min(1.5, max(0.7, (avg_recent + 50) / 100))
        adjusted_base = base_stock * variability_factor
    else:
        adjusted_base = base_stock

    # Calculate target with safety stock and demand buffer
    target_position = adjusted_base * demand_buffer + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_position - inventory_position)

    # Apply smoothing with minimum order threshold
    if raw_order > 20:  # Minimum order threshold
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
