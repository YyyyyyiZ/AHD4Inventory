# policy_hash: 554dbc95d51b240b8cf6f763bc926e38659d9baebdef8f45137739d087d7437d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 11901.0
# best_prompt_performance: 11901.0
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_061206.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 400.00089426081075  # OPT_PARAM: {"initial": 400.00089426081075, "min": 400, "max": 800, "type": "float"}
    pipeline_weight = 0.8218588999632448  # OPT_PARAM: {"initial": 0.8218588999632448, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}
    demand_buffer = 1.288152758861506  # OPT_PARAM: {"initial": 1.288152758861506, "min": 1.2, "max": 2.5, "type": "float"}
    pipeline_threshold = 399.2722548934051  # OPT_PARAM: {"initial": 399.2722548934051, "min": 100, "max": 400, "type": "float"}
    min_order = 20  # OPT_PARAM: {"initial": 20, "min": 0, "max": 50, "type": "int"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate pipeline demand intensity
    total_pipeline = sum(pipeline_orders)
    avg_pipeline_demand = 0.0
    if len(pipeline_orders) > 0:
        avg_pipeline_demand = total_pipeline / len(pipeline_orders)

    # Dynamic adjustment based on pipeline intensity
    adjustment_factor = 0.0
    if avg_pipeline_demand > 0:
        # More aggressive adjustment for high pipeline demand
        if total_pipeline > pipeline_threshold:
            adjustment_factor = min(2.0, (total_pipeline / pipeline_threshold) * 0.5) * demand_buffer
        else:
            adjustment_factor = min(1.0, avg_pipeline_demand / 150.0) * demand_buffer

    # Calculate order-up-to level
    order_up_to = base_stock * (1.0 + adjustment_factor)

    # Calculate raw order amount
    raw_order = max(0.0, order_up_to - inventory_position)

    # Apply smoothing with minimum order threshold
    if raw_order > min_order:
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = 0.0

    # Ensure minimum order size when ordering
    if order_amount > 0 and order_amount < min_order:
        order_amount = min_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
