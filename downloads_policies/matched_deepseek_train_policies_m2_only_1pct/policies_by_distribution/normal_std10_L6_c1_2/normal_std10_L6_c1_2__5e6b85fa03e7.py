# policy_hash: 5e6b85fa03e7615ed813281c7a6351bd4019af4d5f7439f8eb1a9bdd0ec22335
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2229.71
# best_prompt_performance: 2226.92
# best_rel_error_pct: 0.125128
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_101130.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 550.0  # OPT_PARAM: {"initial": 550.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 300.0  # OPT_PARAM: {"initial": 300.0, "min": 50, "max": 300, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Expected demand during lead time
    avg_demand = 110.80559801786302  # OPT_PARAM: {"initial": 110.80559801786302, "min": 80, "max": 120, "type": "float"}
    lead_time = len(pipeline_orders)
    lead_time_demand = avg_demand * lead_time

    # Calculate order-up-to level with dynamic adjustment
    pipeline_coverage = sum(pipeline_orders) / max(1, lead_time_demand)
    adjustment_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 1.2, "type": "float"}

    # Base stock adjustment based on pipeline coverage
    if pipeline_coverage < 0.8:
        adjustment = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.8, "max": 1.3, "type": "float"}
    elif pipeline_coverage > 1.2:
        adjustment = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.7, "max": 1.0, "type": "float"}
    else:
        adjustment = 1.0

    order_up_to = base_stock * adjustment_factor * adjustment

    # Ensure minimum coverage
    min_coverage = lead_time_demand + safety_stock
    order_up_to = max(order_up_to, min_coverage)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with threshold
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    threshold = 20.1  # OPT_PARAM: {"initial": 20.1, "min": 5, "max": 50, "type": "float"}

    if raw_order > threshold:
        smoothed_order = smoothing_factor * raw_order
    else:
        smoothed_order = raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
