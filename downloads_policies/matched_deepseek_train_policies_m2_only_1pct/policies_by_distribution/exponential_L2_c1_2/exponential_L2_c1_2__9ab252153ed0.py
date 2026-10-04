# policy_hash: 9ab252153ed08e20cdf6517f780dad474faa360a45af1c8becfe6c21b9795686
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 6276.22
# best_prompt_performance: 6276.21
# best_rel_error_pct: 0.000159
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_023848.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 188.78367378075046  # OPT_PARAM: {"initial": 188.78367378075046, "min": 150, "max": 350, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    safety_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 2.0, "type": "float"}
    demand_buffer = 20.203621626227864  # OPT_PARAM: {"initial": 20.203621626227864, "min": 20, "max": 100, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic adjustment based on imminent arrival
    next_arrival = pipeline_orders[0]
    if next_arrival > 0:
        # When order arrives, we can be more aggressive
        adjusted_base = base_stock
    else:
        # No immediate arrival, need more buffer
        adjusted_base = base_stock * safety_factor

    # Add demand buffer for uncertainty
    target_position = adjusted_base + demand_buffer

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply integer rounding
    return order_amount
