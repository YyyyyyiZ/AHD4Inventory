# policy_hash: 7b9ac82968df65109881e0dda85237c3daeff857b785ccf192d7bb4e5ee05ea8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 11975.22
# best_prompt_performance: 11961.56
# best_rel_error_pct: 0.114069
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_060742.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 485.32168331741855  # OPT_PARAM: {"initial": 485.32168331741855, "min": 300, "max": 600, "type": "float"}
    safety_stock = 133.2157974428868  # OPT_PARAM: {"initial": 133.2157974428868, "min": 40, "max": 150, "type": "float"}
    pipeline_weight = 0.9330143941634158  # OPT_PARAM: {"initial": 0.9330143941634158, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.9, "type": "float"}

    # Calculate inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Simple order-up-to level
    order_up_to = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing
    if raw_order > 0:
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = 0.0

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
