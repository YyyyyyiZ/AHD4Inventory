# policy_hash: 9cd13d84d7ba1267f2006158d8d5664c012af3760d667c670d3b03bd5a1afd78
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 35
# source_prompt_files: 1
# best_target_performance: 5946.87
# best_prompt_performance: 5947.04
# best_rel_error_pct: 0.002859
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_224255.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 270.7448856052479  # OPT_PARAM: {"initial": 270.7448856052479, "min": 200, "max": 400, "type": "float"}
    safety_stock = 60.0  # OPT_PARAM: {"initial": 60.0, "min": 30, "max": 120, "type": "float"}
    demand_smoothing = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.5, "max": 1.0, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    lost_sales_weight = 1.3  # OPT_PARAM: {"initial": 1.3, "min": 1.0, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage with weighted average
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

    # Adjust base stock based on pipeline coverage and lost sales risk
    # More aggressive adjustment when pipeline is low
    pipeline_adjustment = demand_smoothing * (base_stock - effective_pipeline)
    adjusted_base_stock = base_stock - pipeline_adjustment

    # Apply safety stock with lost sales weighting
    # Higher lost_sales_weight increases target inventory to prevent stockouts
    target_inventory = max(adjusted_base_stock, safety_stock * lost_sales_weight)

    # Calculate order amount with smoother adjustment
    order_gap = target_inventory - inventory_position
    if order_gap > 0:
        order_amount = order_gap * adjustment_factor
    else:
        order_amount = 0

    # Round to nearest integer (maintain non-negative)
    order_amount = max(0, int(round(order_amount)))

    return order_amount
