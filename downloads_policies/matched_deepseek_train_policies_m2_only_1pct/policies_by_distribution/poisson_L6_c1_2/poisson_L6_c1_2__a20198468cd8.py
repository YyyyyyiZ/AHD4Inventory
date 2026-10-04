# policy_hash: a20198468cd8e4b8f8801891d9fd05380c3845959287e4c64e24ddc53dd85ab3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 21
# source_prompt_files: 2
# best_target_performance: 1156.84
# best_prompt_performance: 1155.97
# best_rel_error_pct: 0.075205
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_012535.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 633.3635561336665  # OPT_PARAM: {"initial": 633.3635561336665, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 19.85107311736266  # OPT_PARAM: {"initial": 19.85107311736266, "min": 0, "max": 200, "type": "float"}
    demand_buffer = 56.546607939994594  # OPT_PARAM: {"initial": 56.546607939994594, "min": 0, "max": 300, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals
    # Weight recent pipeline orders more heavily as demand indicators
    weighted_pipeline_sum = 0
    for i, order in enumerate(pipeline_orders):
        weight = 0.4974945382885925  # OPT_PARAM: {"initial": 0.4974945382885925, "min": 0, "max": 2, "type": "float"}
        weighted_pipeline_sum += order * weight

    # Adjust base stock based on pipeline pattern
    pipeline_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}
    if weighted_pipeline_sum > 0:
        avg_pipeline = weighted_pipeline_sum / len(pipeline_orders)
        if avg_pipeline > demand_buffer:
            # Higher pipeline suggests higher future demand
            adjusted_base = 2.0  # Optimized
        else:
            # Lower pipeline suggests lower future demand
            adjusted_base = base_stock * (2.0 - pipeline_factor)  # OPT_PARAM: {"initial": 2.0, "min": 1.5, "max": 2.5, "type": "float"}
    else:
        adjusted_base = base_stock

    # Calculate order amount with safety stock consideration
    target_inventory = adjusted_base + safety_stock
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    if order_amount > 0:
        # Smooth large orders
        order_amount = order_amount * smoothing_factor + (1 - smoothing_factor) * demand_buffer

    return order_amount
