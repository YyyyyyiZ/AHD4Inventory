# policy_hash: c1a9ca821eabe434bd874de38e08443937edb9ca9177b6e5acd64f1ee765150b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2213.75
# best_prompt_performance: 2221.12
# best_rel_error_pct: 0.332919
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_103548.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 520.0  # OPT_PARAM: {"initial": 520.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 277.99139876144494  # OPT_PARAM: {"initial": 277.99139876144494, "min": 50, "max": 300, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Expected demand during lead time
    avg_demand = 115.89616237329473  # OPT_PARAM: {"initial": 115.89616237329473, "min": 80, "max": 120, "type": "float"}
    lead_time = len(pipeline_orders)
    lead_time_demand = avg_demand * lead_time

    # Calculate order-up-to level
    order_up_to = base_stock

    # Dynamic adjustment based on pipeline coverage
    pipeline_coverage = sum(pipeline_orders) / max(1, lead_time_demand)
    if pipeline_coverage < 0.7:
        adjustment = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.8, "max": 1.3, "type": "float"}
    elif pipeline_coverage > 1.3:
        adjustment = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.7, "max": 1.0, "type": "float"}
    else:
        adjustment = 1.0

    order_up_to = order_up_to * adjustment

    # Ensure minimum coverage
    min_coverage = lead_time_demand + safety_stock
    order_up_to = max(order_up_to, min_coverage)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    threshold = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 50, "type": "float"}

    if raw_order > threshold:
        smoothed_order = smoothing_factor * raw_order
    else:
        smoothed_order = raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
