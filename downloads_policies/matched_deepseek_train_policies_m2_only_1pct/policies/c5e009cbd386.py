# policy_hash: c5e009cbd386769dcc0bee65cbdb07d0dd619447f9970eae824b33e7de893e6b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 5941.16
# best_prompt_performance: 5941.16
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_024736.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 180.50257401233978  # OPT_PARAM: {"initial": 180.50257401233978, "min": 100, "max": 300, "type": "float"}
    safety_stock = 40.502574012339736  # OPT_PARAM: {"initial": 40.502574012339736, "min": 10, "max": 100, "type": "float"}
    smoothing_factor = 0.19006769419088218  # OPT_PARAM: {"initial": 0.19006769419088218, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Target inventory level
    target = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target - inventory_position)

    # Apply smoothing with last order placed
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
