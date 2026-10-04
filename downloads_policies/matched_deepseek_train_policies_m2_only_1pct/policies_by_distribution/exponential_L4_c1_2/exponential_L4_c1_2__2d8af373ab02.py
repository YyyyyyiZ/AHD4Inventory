# policy_hash: 2d8af373ab021dcd36aae2cb81a3c6388de1b6dcf8dcdd341c21673d76529983
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 6199.1
# best_prompt_performance: 6199.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_235925.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 244.8564771004727  # OPT_PARAM: {"initial": 244.8564771004727, "min": 100, "max": 500, "type": "float"}
    safety_stock = 4.856477100474885  # OPT_PARAM: {"initial": 4.856477100474885, "min": 0, "max": 100, "type": "float"}
    pipeline_weight = 0.6997377781766786  # OPT_PARAM: {"initial": 0.6997377781766786, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_inventory = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock

    # Calculate base order amount
    order_amount = max(0, target_inventory - effective_inventory)

    # Apply smoothing using average of recent orders
    if pipeline_orders:
        avg_past_order = sum(pipeline_orders) / len(pipeline_orders)
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_past_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
