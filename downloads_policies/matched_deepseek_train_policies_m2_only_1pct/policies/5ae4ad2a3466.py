# policy_hash: 5ae4ad2a3466376cf06c498a7945c2df476ba284df7905b279e73290356710d3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 10288.54
# best_prompt_performance: 10282.85
# best_rel_error_pct: 0.055304
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_033739.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 321.1135547929283  # OPT_PARAM: {"initial": 321.1135547929283, "min": 250, "max": 400, "type": "float"}
    safety_stock = 16.113554792936554  # OPT_PARAM: {"initial": 16.113554792936554, "min": 10, "max": 40, "type": "float"}
    pipeline_weight = 0.43360529573753664  # OPT_PARAM: {"initial": 0.43360529573753664, "min": 0.2, "max": 0.7, "type": "float"}
    smoothing = 0.3172244841885256  # OPT_PARAM: {"initial": 0.3172244841885256, "min": 0.3, "max": 0.8, "type": "float"}
    demand_anticipation = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.05, "max": 0.4, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple pipeline adjustment factor
    if pipeline_orders:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        # Factor decreases as pipeline increases (to avoid over-ordering)
        pipeline_factor = max(0.5, 1.0 - pipeline_weight * (avg_pipeline / base_stock))
    else:
        pipeline_factor = 1.0

    # Target inventory calculation
    target_inventory = base_stock * pipeline_factor + safety_stock

    # Add demand anticipation based on recent pipeline
    if len(pipeline_orders) >= 2:
        recent_avg = sum(pipeline_orders[-2:]) / 2
        target_inventory += demand_anticipation * recent_avg

    # Calculate raw order
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with recent order history
    if pipeline_orders:
        recent_order = pipeline_orders[-1] if pipeline_orders else 0
        smoothed_order = smoothing * raw_order + (1 - smoothing) * recent_order
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    return order_amount
