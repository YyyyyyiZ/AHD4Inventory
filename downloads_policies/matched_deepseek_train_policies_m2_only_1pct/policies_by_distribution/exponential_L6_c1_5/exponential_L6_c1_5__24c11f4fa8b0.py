# policy_hash: 24c11f4fa8b0088ed70a933e06131918a70bbfbe412b7245c7aa057d2ac77b22
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 11830.04
# best_prompt_performance: 11830.04
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_101351.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 446.3115651989156  # OPT_PARAM: {"initial": 446.3115651989156, "min": 300, "max": 600, "type": "float"}
    safety_stock = 71.3115651989183  # OPT_PARAM: {"initial": 71.3115651989183, "min": 50, "max": 150, "type": "float"}
    demand_estimate = 119.21851650995757  # OPT_PARAM: {"initial": 119.21851650995757, "min": 90, "max": 180, "type": "float"}
    pipeline_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.9, "type": "float"}
    recent_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.2, "max": 0.6, "type": "float"}
    min_order_factor = 0.67279586583362  # OPT_PARAM: {"initial": 0.67279586583362, "min": 0.3, "max": 0.8, "type": "float"}
    max_order_factor = 2.2513749587548393  # OPT_PARAM: {"initial": 2.2513749587548393, "min": 1.5, "max": 4.0, "type": "float"}
    smoothing_factor = 0.6156203977781309  # OPT_PARAM: {"initial": 0.6156203977781309, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate pipeline characteristics
    total_pipeline = sum(pipeline_orders)
    recent_pipeline = sum(pipeline_orders[:3])  # Next 3 periods' arrivals

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
