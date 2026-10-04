# policy_hash: 7350d6ca534214ec99f728cf3feedabe6cee8855649fa33d2a918061b8f5a8af
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 12404.66
# best_prompt_performance: 12404.66
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_101941.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 380.0  # OPT_PARAM: {"initial": 380.0, "min": 300, "max": 450, "type": "float"}
    safety_stock = 60.0  # OPT_PARAM: {"initial": 60.0, "min": 40, "max": 100, "type": "float"}
    demand_estimate = 130.0  # OPT_PARAM: {"initial": 130.0, "min": 100, "max": 160, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.5, "max": 0.9, "type": "float"}
    min_order_factor = 0.8241674219973867  # OPT_PARAM: {"initial": 0.8241674219973867, "min": 0.6, "max": 1.2, "type": "float"}
    max_order_factor = 2.2930159595497295  # OPT_PARAM: {"initial": 2.2930159595497295, "min": 2.0, "max": 3.5, "type": "float"}
    smoothing_factor = 0.6302645421415611  # OPT_PARAM: {"initial": 0.6302645421415611, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate total pipeline
    total_pipeline = sum(pipeline_orders)

    # Dynamic target adjustment: reduce base stock when pipeline is high
    # More aggressive pipeline weighting to prevent over-ordering
    pipeline_adjustment = pipeline_weight * total_pipeline

    # Calculate target inventory position
    target_position = base_stock + safety_stock - pipeline_adjustment

    # Calculate base order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply demand-based minimum order
    min_order = min_order_factor * demand_estimate
    max_order = max_order_factor * demand_estimate

    # Smooth adjustment towards minimum order when below threshold
    if order_amount < min_order:
        order_amount = smoothing_factor * min_order + (1 - smoothing_factor) * order_amount

    # Cap maximum order to avoid excessive inventory buildup
    order_amount = min(order_amount, max_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
