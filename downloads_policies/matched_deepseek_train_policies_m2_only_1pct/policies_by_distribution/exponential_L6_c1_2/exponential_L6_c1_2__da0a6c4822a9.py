# policy_hash: da0a6c4822a9d49c5623e49a25d6546713faf19f76920dc425f6632e841330f1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 6090.69
# best_prompt_performance: 6090.69
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_055138.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 442.8399962645898  # OPT_PARAM: {"initial": 442.8399962645898, "min": 300, "max": 450, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.9, "max": 1.1, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    safety_stock = 96.510112151343  # OPT_PARAM: {"initial": 96.510112151343, "min": 40, "max": 100, "type": "float"}
    demand_forecast_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_lookahead = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 6, "type": "int"}

    # Calculate effective pipeline with full weight
    effective_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Estimate upcoming demand from near-term pipeline arrivals only
    near_term_pipeline = sum(pipeline_orders[:pipeline_lookahead])
    upcoming_demand_estimate = near_term_pipeline * demand_forecast_factor

    # Dynamic target level
    dynamic_target = base_stock + safety_stock + upcoming_demand_estimate

    # Calculate raw order amount
    raw_order = max(0, dynamic_target - inventory_position)

    # Apply smoothing to all orders for stability
    order_amount = smoothing_factor * raw_order

    # Round to nearest integer
    return order_amount
