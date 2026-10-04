# policy_hash: f3ae08154aab1e582f390344de027ba1486dba45ef51cda577b5c378c1b24141
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 11264.49
# best_prompt_performance: 11264.49
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_062528.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 644.7671945909052  # OPT_PARAM: {"initial": 644.7671945909052, "min": 400, "max": 900, "type": "float"}
    safety_stock = 162.63602579120558  # OPT_PARAM: {"initial": 162.63602579120558, "min": 100, "max": 350, "type": "float"}
    pipeline_coverage_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.3, "type": "float"}
    smoothing_factor = 0.15000000000000002  # OPT_PARAM: {"initial": 0.15000000000000002, "min": 0.05, "max": 0.3, "type": "float"}
    lost_sales_weight = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 2.0, "max": 5.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline coverage
    pipeline_total = sum(pipeline_orders)
    adjusted_base_stock = base_stock * (1 + pipeline_coverage_factor * (1 - pipeline_total / max(1, base_stock)))

    # Calculate target inventory with lost sales weighting
    target_inventory = adjusted_base_stock + safety_stock * lost_sales_weight

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme fluctuations
    if order_amount > 0:
        order_amount = order_amount * smoothing_factor

    return order_amount
