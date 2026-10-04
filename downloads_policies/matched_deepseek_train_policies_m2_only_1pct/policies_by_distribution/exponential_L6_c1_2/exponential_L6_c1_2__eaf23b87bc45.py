# policy_hash: eaf23b87bc456ece687510e25efa52ca4d437a1fbfb183d82a04119914b14c63
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 6095.08
# best_prompt_performance: 6095.08
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_054904.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 432.47233249993144  # OPT_PARAM: {"initial": 432.47233249993144, "min": 350, "max": 500, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.9, "max": 1.1, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    safety_stock = 92.47233249993852  # OPT_PARAM: {"initial": 92.47233249993852, "min": 60, "max": 120, "type": "float"}
    demand_forecast_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_lookahead = 4  # OPT_PARAM: {"initial": 4, "min": 1, "max": 6, "type": "int"}
    min_order_threshold = 19.994426346718477  # OPT_PARAM: {"initial": 19.994426346718477, "min": 10, "max": 50, "type": "float"}

    # Calculate effective pipeline with full weight
    effective_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Estimate upcoming demand from near-term pipeline arrivals
    near_term_pipeline = sum(pipeline_orders[:pipeline_lookahead])
    upcoming_demand_estimate = near_term_pipeline * demand_forecast_factor

    # Dynamic target level with reduced safety stock
    dynamic_target = base_stock + safety_stock + upcoming_demand_estimate

    # Calculate raw order amount
    raw_order = max(0, dynamic_target - inventory_position)

    # Apply smoothing with higher factor for more responsiveness
    order_amount = smoothing_factor * raw_order

    # Apply minimum order threshold to avoid tiny orders
    if order_amount < min_order_threshold:
        order_amount = 0

    # Round to nearest integer
    return order_amount
