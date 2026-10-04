# policy_hash: 076d002ec7960f706a5d386fe7a44f90fe187aba9538ffeef36b875b719e7051
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 25
# source_prompt_files: 1
# best_target_performance: 5932.36
# best_prompt_performance: 5932.36
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_224648.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 183.7054649131569  # OPT_PARAM: {"initial": 183.7054649131569, "min": 100, "max": 300, "type": "float"}
    safety_stock = 25.0  # OPT_PARAM: {"initial": 25.0, "min": 10, "max": 80, "type": "float"}
    demand_smoothing = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.95  # OPT_PARAM: {"initial": 0.95, "min": 0.3, "max": 1.0, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    lost_sales_weight = 1.547703453026909  # OPT_PARAM: {"initial": 1.547703453026909, "min": 1.0, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline coverage
    weighted_pipeline = 0
    total_weight = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
        weighted_pipeline += order * weight
        total_weight += weight

    if total_weight > 0:
        effective_pipeline = weighted_pipeline / total_weight
    else:
        effective_pipeline = 0

    # Adjust base stock based on pipeline and lost-sales penalty
    # Higher lost_sales_weight increases target inventory when p > h
    pipeline_adjustment = demand_smoothing * (base_stock * lost_sales_weight - effective_pipeline)
    adjusted_base_stock = base_stock * lost_sales_weight - pipeline_adjustment

    # Apply safety stock floor
    target_inventory = max(adjusted_base_stock, safety_stock)

    # Calculate order amount with more aggressive adjustment
    order_gap = target_inventory - inventory_position
    if order_gap > 0:
        order_amount = order_gap * adjustment_factor
    else:
        order_amount = 0

    # Round to nearest integer (maintain non-negative)
    order_amount = max(0, int(round(order_amount)))

    return order_amount
