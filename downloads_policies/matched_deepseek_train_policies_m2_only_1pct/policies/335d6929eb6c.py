# policy_hash: 335d6929eb6cb6450eb7014863445a67b7ebd5c3e77f5b94f314ab19f070e3ef
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 12291.56
# best_prompt_performance: 12291.56
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_102101.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 380.0  # OPT_PARAM: {"initial": 380.0, "min": 300, "max": 450, "type": "float"}
    safety_stock = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 60, "max": 120, "type": "float"}
    demand_estimate = 118.85407750633098  # OPT_PARAM: {"initial": 118.85407750633098, "min": 100, "max": 150, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.5, "max": 0.9, "type": "float"}
    recent_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.5, "type": "float"}
    min_order_factor = 0.8508326200506479  # OPT_PARAM: {"initial": 0.8508326200506479, "min": 0.6, "max": 1.0, "type": "float"}
    max_order_factor = 2.37708155012662  # OPT_PARAM: {"initial": 2.37708155012662, "min": 2.0, "max": 3.5, "type": "float"}
    smoothing_factor = 0.6508326200506479  # OPT_PARAM: {"initial": 0.6508326200506479, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate pipeline characteristics
    total_pipeline = sum(pipeline_orders)
    recent_pipeline = sum(pipeline_orders[:2])  # Next 2 periods' arrivals (reduced from 3)

    # Dynamic target adjustment based on pipeline
    pipeline_adjustment = pipeline_weight * total_pipeline
    recent_adjustment = recent_weight * recent_pipeline

    # Calculate target inventory position
    target_position = base_stock + safety_stock - pipeline_adjustment + recent_adjustment

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
