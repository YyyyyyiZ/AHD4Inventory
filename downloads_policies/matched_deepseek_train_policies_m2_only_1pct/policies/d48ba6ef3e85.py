# policy_hash: d48ba6ef3e853dd1eeee3de8965df3ea6af1d4c2e331763a607f8a6ca7f7bcb3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 6023.73
# best_prompt_performance: 6023.73
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_041804.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 280.87963671034424  # OPT_PARAM: {"initial": 280.87963671034424, "min": 250, "max": 320, "type": "float"}
    pipeline_weight = 0.947256198791979  # OPT_PARAM: {"initial": 0.947256198791979, "min": 0.85, "max": 0.98, "type": "float"}
    demand_buffer = 1.0348747807775105  # OPT_PARAM: {"initial": 1.0348747807775105, "min": 1.0, "max": 1.15, "type": "float"}
    smoothing_factor = 0.18572311987192247  # OPT_PARAM: {"initial": 0.18572311987192247, "min": 0.15, "max": 0.35, "type": "float"}
    safety_stock = 41.6824770427294  # OPT_PARAM: {"initial": 41.6824770427294, "min": 35, "max": 55, "type": "float"}
    pipeline_decay = 0.9749440270639862  # OPT_PARAM: {"initial": 0.9749440270639862, "min": 0.8, "max": 1.0, "type": "float"}
    recent_weight = 0.7849034830094523  # OPT_PARAM: {"initial": 0.7849034830094523, "min": 0.6, "max": 0.85, "type": "float"}
    lost_sales_weight = 1.2035719219490395  # OPT_PARAM: {"initial": 1.2035719219490395, "min": 1.05, "max": 1.25, "type": "float"}

    # Calculate weighted pipeline with exponential decay
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_decay ** i
        weighted_pipeline += order * weight
    weighted_pipeline *= pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Adjust base stock based on lost sales cost ratio
    adjusted_base_stock = base_stock * lost_sales_weight

    # Calculate target inventory
    target_inventory = adjusted_base_stock * demand_buffer + safety_stock

    # Base order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing with weighted recent pipeline
    if len(pipeline_orders) > 0:
        if len(pipeline_orders) >= 2:
            recent_pipeline = recent_weight * pipeline_orders[0] + (1 - recent_weight) * pipeline_orders[1]
        else:
            recent_pipeline = pipeline_orders[0]

        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_pipeline
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    return order_amount
