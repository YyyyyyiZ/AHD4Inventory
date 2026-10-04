# policy_hash: 9f73482ecb4d996527153c4e7a74a664d65045953adb753cffce793c3d2cb22b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 6087.18
# best_prompt_performance: 6089.44
# best_rel_error_pct: 0.037127
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_093455.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 486.8750289307117  # OPT_PARAM: {"initial": 486.8750289307117, "min": 350, "max": 550, "type": "float"}
    pipeline_weight = 0.9140925414526769  # OPT_PARAM: {"initial": 0.9140925414526769, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.6, "type": "float"}
    safety_stock = 51.746274063655655  # OPT_PARAM: {"initial": 51.746274063655655, "min": 30, "max": 100, "type": "float"}
    demand_buffer = 1.0485546342099308  # OPT_PARAM: {"initial": 1.0485546342099308, "min": 1.0, "max": 1.5, "type": "float"}
    min_order_threshold = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 5, "max": 30, "type": "float"}

    # Calculate effective pipeline with weighted sum
    effective_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Simple base stock adjustment based on pipeline variability
    if len(pipeline_orders) >= 2:
        recent_avg = sum(pipeline_orders[:2]) / 2
        variability_factor = min(1.3, max(0.8, (recent_avg + 30) / 80))
        adjusted_base = base_stock * variability_factor
    else:
        adjusted_base = base_stock

    # Calculate target with safety stock and demand buffer
    target_position = adjusted_base * demand_buffer + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_position - inventory_position)

    # Apply smoothing with minimum order threshold
    if raw_order > min_order_threshold:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
