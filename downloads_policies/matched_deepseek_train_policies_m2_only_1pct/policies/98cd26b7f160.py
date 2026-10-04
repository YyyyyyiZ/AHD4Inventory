# policy_hash: 98cd26b7f16027cba425a70489cf01b901c425e31ce2b1c3d6246b5efd00637c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 11025.46
# best_prompt_performance: 11024.96
# best_rel_error_pct: 0.004535
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_084811.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 546.792880367991  # OPT_PARAM: {"initial": 546.792880367991, "min": 300, "max": 700, "type": "float"}
    pipeline_weight = 0.6204818145742924  # OPT_PARAM: {"initial": 0.6204818145742924, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.4, "type": "float"}
    safety_stock = 181.79288036800847  # OPT_PARAM: {"initial": 181.79288036800847, "min": 50, "max": 250, "type": "float"}
    demand_anticipation = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Add safety stock to base stock level
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order-up-to amount
    order_up_to = max(0, adjusted_base_stock - inventory_position)

    # Apply demand anticipation: increase orders when pipeline is low
    if sum(pipeline_orders) < 0.3 * adjusted_base_stock:
        order_up_to *= (1 + demand_anticipation)

    # Apply smoothing with stronger effect for larger orders
    if order_up_to > 100:
        smoothing_factor = max(0.15, smoothing_factor * 0.8)

    order_amount = smoothing_factor * order_up_to

    # Round to nearest integer (as order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
