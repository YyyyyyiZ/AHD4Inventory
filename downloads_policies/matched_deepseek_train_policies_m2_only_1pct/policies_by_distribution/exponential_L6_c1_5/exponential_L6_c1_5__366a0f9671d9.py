# policy_hash: 366a0f9671d9e3d9f8226afd35c2ae5ae5796aab23387d6d706b40c3baa29965
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 11513.28
# best_prompt_performance: 11513.28
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_060010.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 540.1964385738402  # OPT_PARAM: {"initial": 540.1964385738402, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 140.95516642297997  # OPT_PARAM: {"initial": 140.95516642297997, "min": 0, "max": 500, "type": "float"}
    demand_forecast_window = 10  # OPT_PARAM: {"initial": 10, "min": 1, "max": 50, "type": "int"}
    forecast_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0, "max": 1, "type": "float"}
    pipeline_weight = 0.1908770639571979  # OPT_PARAM: {"initial": 0.1908770639571979, "min": 0, "max": 2, "type": "float"}
    adjustment_factor = 0.7786718226611142  # OPT_PARAM: {"initial": 0.7786718226611142, "min": 0, "max": 2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline coverage
    pipeline_coverage = sum(pipeline_orders) / max(1, base_stock)
    adjusted_base_stock = base_stock * (1 + adjustment_factor * (1 - pipeline_coverage))

    # Add safety stock
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    if order_amount > 0:
        order_amount = max(0, order_amount * pipeline_weight)

    return order_amount
