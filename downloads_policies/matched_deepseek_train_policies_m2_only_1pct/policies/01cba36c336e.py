# policy_hash: 01cba36c336ee323c32dcb490c5928533612ed3d1dbe43c71d6af52617fa1f3a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 11338.9
# best_prompt_performance: 11338.9
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_062002.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 629.0789716992781  # OPT_PARAM: {"initial": 629.0789716992781, "min": 400, "max": 900, "type": "float"}
    safety_stock = 186.35528018946553  # OPT_PARAM: {"initial": 186.35528018946553, "min": 100, "max": 350, "type": "float"}
    pipeline_coverage_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.3, "type": "float"}
    smoothing_factor = 0.19999999999999998  # OPT_PARAM: {"initial": 0.19999999999999998, "min": 0.05, "max": 0.3, "type": "float"}
    lost_sales_weight = 5.0  # OPT_PARAM: {"initial": 5.0, "min": 2.0, "max": 5.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate pipeline coverage adjustment
    pipeline_total = sum(pipeline_orders)
    adjusted_base_stock = base_stock * (1 - pipeline_coverage_factor * min(1.0, pipeline_total / max(1, base_stock)))

    # Calculate target inventory with safety stock adjustment
    target_inventory = adjusted_base_stock + safety_stock * (lost_sales_weight / 5.0)

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with threshold
    if raw_order > 0:
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = 0

    # Round to nearest integer (as order quantities should be integers)
    return order_amount
