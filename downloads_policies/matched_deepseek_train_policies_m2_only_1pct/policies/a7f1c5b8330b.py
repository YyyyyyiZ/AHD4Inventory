# policy_hash: a7f1c5b8330bfd5b9293e62a2de2b05a31fe35a41b54354483b3cfaecf37b842
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 6170.5
# best_prompt_performance: 6170.48
# best_rel_error_pct: 0.000324
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_052932.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 357.177088897703  # OPT_PARAM: {"initial": 357.177088897703, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.653307436827156  # OPT_PARAM: {"initial": 50.653307436827156, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 0.6549835995211281  # OPT_PARAM: {"initial": 0.6549835995211281, "min": 0.1, "max": 1.5, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    pipeline_std_weight = 0.14692064779096395  # OPT_PARAM: {"initial": 0.14692064779096395, "min": 0.0, "max": 0.5, "type": "float"}
    demand_forecast_weight = 0.7396119179222529  # OPT_PARAM: {"initial": 0.7396119179222529, "min": 0.0, "max": 1.0, "type": "float"}
    min_order_threshold = 10  # OPT_PARAM: {"initial": 10, "min": 0, "max": 50, "type": "int"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate pipeline variability adjustment
    if len(pipeline_orders) > 1:
        pipeline_mean = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_std = sum((q - pipeline_mean) ** 2 for q in pipeline_orders) ** 0.5
        std_adjustment = safety_stock * min(1.0, pipeline_std * pipeline_std_weight)
    else:
        std_adjustment = 0

    # Calculate target inventory position
    adjusted_base = base_stock + std_adjustment
    target = max(0, adjusted_base - inventory_position)

    # Apply smoothing
    if target > 0:
        order_amount = max(0, smoothing_factor * target)
    else:
        order_amount = 0

    # Add demand-responsive adjustment based on recent pipeline
    if len(pipeline_orders) > 0:
        recent_demand_estimate = sum(pipeline_orders) / len(pipeline_orders)
        demand_adjustment = demand_forecast_weight * recent_demand_estimate
        order_amount = max(order_amount, demand_adjustment)

    # Apply minimum order threshold to reduce small, frequent orders
    if order_amount < min_order_threshold:
        order_amount = 0

    return order_amount
