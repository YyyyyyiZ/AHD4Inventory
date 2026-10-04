# policy_hash: 7d51253af72aee25816bf6bcc003433fa338ecd66cb265db134934dc62bd20a6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 26
# source_prompt_files: 1
# best_target_performance: 11013.12
# best_prompt_performance: 11013.06
# best_rel_error_pct: 0.000545
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_090709.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 541.5587019628504  # OPT_PARAM: {"initial": 541.5587019628504, "min": 400, "max": 800, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    safety_stock = 171.42197105186597  # OPT_PARAM: {"initial": 171.42197105186597, "min": 100, "max": 300, "type": "float"}
    lost_sales_weight = 0.5504040037511024  # OPT_PARAM: {"initial": 0.5504040037511024, "min": 0.5, "max": 1.0, "type": "float"}
    min_order_size = 15  # OPT_PARAM: {"initial": 15, "min": 5, "max": 30, "type": "int"}

    # Calculate effective inventory position
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic safety stock adjustment
    if len(pipeline_orders) > 1:
        pipeline_range = max(pipeline_orders) - min(pipeline_orders)
        pipeline_variability = min(0.4, pipeline_range / 300.0)
        dynamic_safety = safety_stock * (1.0 + pipeline_variability)
    else:
        dynamic_safety = safety_stock

    # Adjust base stock with lost sales consideration
    adjusted_base_stock = base_stock + dynamic_safety * lost_sales_weight

    # Calculate order-up-to amount
    order_up_to = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing
    order_amount = smoothing_factor * order_up_to

    # Apply minimum order size
    if order_amount > 0 and order_amount < min_order_size:
        order_amount = min_order_size

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
