# policy_hash: 0107583364f891a38ccffa1d0e72bcc280fb70ab4f686aa564ac9823d1950d66
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 19
# source_prompt_files: 1
# best_target_performance: 3518.74
# best_prompt_performance: 3520.75
# best_rel_error_pct: 0.057123
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_020759.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 657.4009891593281  # OPT_PARAM: {"initial": 657.4009891593281, "min": 500, "max": 800, "type": "float"}
    safety_stock = 20.000000000000007  # OPT_PARAM: {"initial": 20.000000000000007, "min": 20, "max": 150, "type": "float"}
    lead_time = 6  # OPT_PARAM: {"initial": 6, "min": 1, "max": 10, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate average pipeline orders (excluding the oldest which arrives now)
    if len(pipeline_orders) > 1:
        avg_pipeline = sum(pipeline_orders[1:]) / (len(pipeline_orders) - 1)
    else:
        avg_pipeline = 0

    # Adjust target based on pipeline variability
    pipeline_variability = max(0, sum(pipeline_orders[1:]) - avg_pipeline * (len(pipeline_orders) - 1))
    variability_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock + variability_adjustment

    # Calculate order amount with smoothing
    order_needed = target_inventory - inventory_position
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    if order_needed > 0:
        order_amount = max(0, order_needed * smoothing_factor)
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
