# policy_hash: e0a140081930fcdb21b5258dd5c3f17ba295ec6141d94a47c8a9add84d1a6277
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 693.41
# best_prompt_performance: 693.41
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260129_211218.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 303.7508445166677  # OPT_PARAM: {"initial": 303.7508445166677, "min": 280, "max": 320, "type": "float"}
    safety_stock = 37.06158805149306  # OPT_PARAM: {"initial": 37.06158805149306, "min": 25, "max": 50, "type": "float"}
    demand_buffer = 13.626974937553106  # OPT_PARAM: {"initial": 13.626974937553106, "min": 12, "max": 25, "type": "float"}
    smoothing_min = 8.0  # OPT_PARAM: {"initial": 8.0, "min": 5, "max": 15, "type": "float"}
    smoothing_max = 97.88775320307505  # OPT_PARAM: {"initial": 97.88775320307505, "min": 70, "max": 120, "type": "float"}
    pipeline_weight = 0.75  # OPT_PARAM: {"initial": 0.75, "min": 0.4, "max": 1.0, "type": "float"}
    adjustment_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline coverage
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Dynamic base stock adjustment
    if on_hand_inventory < safety_stock:
        # More aggressive ordering when inventory is low
        adjusted_base = base_stock + demand_buffer * 1.5
    elif weighted_pipeline < base_stock * 0.3:
        # Higher base when pipeline coverage is insufficient
        adjusted_base = base_stock + safety_stock * adjustment_factor
    else:
        # Normal operation - smaller adjustment
        adjusted_base = base_stock - demand_buffer * 0.2

    # Calculate order amount
    order_amount = max(0, adjusted_base - inventory_position)

    # Apply smoothing with tighter bounds
    if order_amount > 0:
        order_amount = max(smoothing_min, min(order_amount, smoothing_max))

    return order_amount
