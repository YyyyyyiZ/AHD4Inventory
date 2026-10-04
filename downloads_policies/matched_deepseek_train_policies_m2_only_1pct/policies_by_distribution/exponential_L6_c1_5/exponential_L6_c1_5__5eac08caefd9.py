# policy_hash: 5eac08caefd9b02964de4515774b0285b32a3c2390a49e99c8ca5d5918fe2a30
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 12097.45
# best_prompt_performance: 12097.19
# best_rel_error_pct: 0.002149
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_015821.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 11.977152342464908  # OPT_PARAM: {"initial": 11.977152342464908, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 73.46666489436578  # OPT_PARAM: {"initial": 73.46666489436578, "min": 0, "max": 500, "type": "float"}
    pipeline_weight = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on pipeline composition
    oldest_order = pipeline_orders[0] if pipeline_orders else 0
    pipeline_imbalance = abs(oldest_order - (sum(pipeline_orders) / len(pipeline_orders))) if len(pipeline_orders) > 0 else 0
    imbalance_factor = 50.541603516895464  # OPT_PARAM: {"initial": 50.541603516895464, "min": 50, "max": 500, "type": "float"}

    adjusted_base_stock = base_stock * imbalance_factor

    # Calculate order amount with safety stock consideration
    target_inventory = adjusted_base_stock + safety_stock
    order_amount = max(0, target_inventory - inventory_position)

    # Smooth ordering to avoid extreme fluctuations
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        avg_recent_orders = sum(pipeline_orders[-3:]) / min(3, len(pipeline_orders)) if len(pipeline_orders) >= 3 else pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_recent_orders
        order_amount = max(0, smoothed_order)

    # Round to nearest integer (as required by output type)
    return order_amount
