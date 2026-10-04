# policy_hash: b3442b74ddaba20177939c5385caa03cbc4068396d181475170f4371ff8054ef
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 12
# source_prompt_files: 2
# best_target_performance: 13808.1
# best_prompt_performance: 13808.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_055822.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 547.0207538099825  # OPT_PARAM: {"initial": 547.0207538099825, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 143.0332140758602  # OPT_PARAM: {"initial": 143.0332140758602, "min": 0, "max": 500, "type": "float"}
    pipeline_weight = 0.4315733816792373  # OPT_PARAM: {"initial": 0.4315733816792373, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate order-up-to level with safety stock adjustment
    order_up_to = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid extreme order sizes
    smoothing_factor = 0.14419271249786145  # OPT_PARAM: {"initial": 0.14419271249786145, "min": 0.1, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = order_amount * smoothing_factor

    # Round to nearest integer (as required by output type)
    order_amount = int(round(order_amount))

    return order_amount
