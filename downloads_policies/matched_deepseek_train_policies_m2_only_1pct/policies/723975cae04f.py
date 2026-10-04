# policy_hash: 723975cae04f5a8a390b5b963851356c50ccca7aa12bc6229c82b7a54bda80bd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 12063.16
# best_prompt_performance: 12063.16
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_101908.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 386.7035543414024  # OPT_PARAM: {"initial": 386.7035543414024, "min": 300, "max": 450, "type": "float"}
    safety_stock = 96.70355434140242  # OPT_PARAM: {"initial": 96.70355434140242, "min": 60, "max": 120, "type": "float"}
    demand_estimate = 129.55168966732353  # OPT_PARAM: {"initial": 129.55168966732353, "min": 100, "max": 150, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 0.9, "type": "float"}
    recent_weight = 0.4296510332086968  # OPT_PARAM: {"initial": 0.4296510332086968, "min": 0.1, "max": 0.5, "type": "float"}
    min_order_factor = 0.5322230706938071  # OPT_PARAM: {"initial": 0.5322230706938071, "min": 0.3, "max": 0.7, "type": "float"}
    max_order_factor = 1.7513566981852409  # OPT_PARAM: {"initial": 1.7513566981852409, "min": 1.5, "max": 3.0, "type": "float"}
    smoothing_factor = 0.95  # OPT_PARAM: {"initial": 0.95, "min": 0.6, "max": 0.95, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate pipeline characteristics
    total_pipeline = sum(pipeline_orders)
    recent_pipeline = sum(pipeline_orders[:2])  # Next 2 periods' arrivals

    # Dynamic target adjustment based on pipeline
    # Higher weight on total pipeline to avoid over-ordering
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
