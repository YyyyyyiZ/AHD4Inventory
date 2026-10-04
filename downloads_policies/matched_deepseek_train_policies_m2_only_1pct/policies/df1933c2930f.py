# policy_hash: df1933c2930f3da3d1db6dd155ade0d1176c3ccfb9dbc8ae5603fbd6f05549b1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 10987.34
# best_prompt_performance: 10987.34
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_090559.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 499.3970608723727  # OPT_PARAM: {"initial": 499.3970608723727, "min": 300, "max": 800, "type": "float"}
    pipeline_weight = 0.8502442368222444  # OPT_PARAM: {"initial": 0.8502442368222444, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    safety_stock = 124.26856783922251  # OPT_PARAM: {"initial": 124.26856783922251, "min": 50, "max": 300, "type": "float"}
    demand_buffer = 1.0970804227403563  # OPT_PARAM: {"initial": 1.0970804227403563, "min": 0.8, "max": 2.0, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate base order with safety stock adjustment
    base_order = max(0, base_stock - inventory_position)

    # Add demand buffer consideration based on recent pipeline
    if len(pipeline_orders) > 0:
        recent_arrivals = pipeline_orders[0] if pipeline_orders[0] > 0 else 0
        buffer_adjustment = demand_buffer * recent_arrivals
        adjusted_order = base_order + safety_stock + buffer_adjustment
    else:
        adjusted_order = base_order + safety_stock

    # Apply smoothing to prevent extreme order fluctuations
    order_amount = smoothing_factor * adjusted_order

    return order_amount
