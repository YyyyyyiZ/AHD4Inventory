# policy_hash: 965bfb104897768409f6dced0395f64c4382d4cfe6d8735717343212bf0698e9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 71
# source_prompt_files: 2
# best_target_performance: 11115.09
# best_prompt_performance: 11115.09
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_061624.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 558.9316195389232  # OPT_PARAM: {"initial": 558.9316195389232, "min": 300, "max": 800, "type": "float"}
    safety_stock = 105.07889566383137  # OPT_PARAM: {"initial": 105.07889566383137, "min": 50, "max": 300, "type": "float"}
    pipeline_weight = 0.6354267608076228  # OPT_PARAM: {"initial": 0.6354267608076228, "min": 0.5, "max": 1.5, "type": "float"}
    smoothing = 0.12067383559649153  # OPT_PARAM: {"initial": 0.12067383559649153, "min": 0.1, "max": 0.5, "type": "float"}
    lost_sales_multiplier = 2.1537634762231486  # OPT_PARAM: {"initial": 2.1537634762231486, "min": 1.5, "max": 3.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust target based on pipeline coverage
    pipeline_total = sum(pipeline_orders)
    adjusted_target = base_stock + safety_stock * lost_sales_multiplier
    if pipeline_total > 0:
        adjusted_target *= (1 + pipeline_weight * pipeline_total / (base_stock + 1))

    # Calculate order amount
    order_amount = max(0, adjusted_target - inventory_position)

    # Apply smoothing
    if order_amount > 0:
        order_amount = order_amount * smoothing

    return order_amount
