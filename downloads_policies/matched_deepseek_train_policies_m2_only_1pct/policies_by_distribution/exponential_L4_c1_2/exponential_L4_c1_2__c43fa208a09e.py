# policy_hash: c43fa208a09ecc1e29d924ed964b343c5929c6d0f948a166b55bd3b36c68374d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 20
# source_prompt_files: 1
# best_target_performance: 6209.46
# best_prompt_performance: 6209.46
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_235406.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 179.00026188648152  # OPT_PARAM: {"initial": 179.00026188648152, "min": 50, "max": 400, "type": "float"}
    safety_stock = 24.000261886481553  # OPT_PARAM: {"initial": 24.000261886481553, "min": 0, "max": 100, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate inventory position with weighted pipeline
    inventory_position = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate base order
    base_order = max(0, target_inventory - inventory_position)

    # Apply smoothing using recent pipeline average
    if pipeline_orders:
        avg_recent_order = sum(pipeline_orders) / len(pipeline_orders)
        smoothed_order = smoothing_factor * base_order + (1 - smoothing_factor) * avg_recent_order
    else:
        smoothed_order = base_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
