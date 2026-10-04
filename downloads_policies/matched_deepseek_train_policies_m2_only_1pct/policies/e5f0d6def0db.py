# policy_hash: e5f0d6def0dbd7e8a7bd5e1fade1c72bd0570231130fd576e7760b20b580cf04
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 30
# source_prompt_files: 1
# best_target_performance: 11147.32
# best_prompt_performance: 11147.32
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_063454.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 384.5693026763428  # OPT_PARAM: {"initial": 384.5693026763428, "min": 200, "max": 600, "type": "float"}
    safety_stock = 139.20126623378565  # OPT_PARAM: {"initial": 139.20126623378565, "min": 80, "max": 300, "type": "float"}
    pipeline_weight = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    lost_sales_multiplier = 3.0  # OPT_PARAM: {"initial": 3.0, "min": 1.5, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline coverage
    pipeline_total = sum(pipeline_orders)
    adjusted_base = base_stock + pipeline_weight * pipeline_total

    # Calculate target inventory with safety stock adjustment
    target = adjusted_base + safety_stock * lost_sales_multiplier

    # Calculate raw order amount
    order_amount = max(0, target - inventory_position)

    # Apply smoothing to order amount
    if order_amount > 0:
        order_amount = order_amount * smoothing

    return order_amount
