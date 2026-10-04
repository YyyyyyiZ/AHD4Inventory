# policy_hash: ebf4eea49c91eb7f4a0614498d0cf71a876eef3f7f89d24385e53647fb788f8e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 6512.56
# best_prompt_performance: 6512.56
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_235439.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 317.9399924593565  # OPT_PARAM: {"initial": 317.9399924593565, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 200, "type": "float"}
    demand_buffer = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 0, "max": 300, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on recent demand pattern in pipeline
    recent_orders = sum(pipeline_orders[-2:]) if len(pipeline_orders) >= 2 else sum(pipeline_orders)
    if recent_orders > demand_buffer:
        adjusted_base = base_stock + safety_stock
    else:
        adjusted_base = base_stock

    # Calculate order amount
    order_amount = max(0, adjusted_base - inventory_position)

    # Smooth ordering to avoid extreme fluctuations
    max_order_increase = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 50, "max": 500, "type": "float"}
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        if order_amount > last_order + max_order_increase:
            order_amount = last_order + max_order_increase

    return order_amount
