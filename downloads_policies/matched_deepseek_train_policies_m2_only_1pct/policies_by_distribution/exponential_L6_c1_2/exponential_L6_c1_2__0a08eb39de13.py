# policy_hash: 0a08eb39de13972c6910acf2c6a307a4a35d239c2f102bf80f03545967ace7ff
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 6105.48
# best_prompt_performance: 6105.48
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_053746.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.392672301381  # OPT_PARAM: {"initial": 450.392672301381, "min": 300, "max": 600, "type": "float"}
    safety_stock = 80.47113784603125  # OPT_PARAM: {"initial": 80.47113784603125, "min": 40, "max": 150, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    min_order_threshold = 10  # OPT_PARAM: {"initial": 10, "min": 0, "max": 30, "type": "int"}
    demand_buffer_factor = 1.261991910508982  # OPT_PARAM: {"initial": 1.261991910508982, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate effective pipeline with weighted adjustment
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic target based on upcoming pipeline and safety stock
    upcoming_pipeline = sum(pipeline_orders[1:]) if len(pipeline_orders) > 1 else 0
    dynamic_target = base_stock + safety_stock * demand_buffer_factor - 0.1 * upcoming_pipeline

    # Calculate order gap
    gap = dynamic_target - inventory_position

    # Apply smoothing with more aggressive ordering
    if gap > 0:
        order_amount = max(0, smoothing_factor * gap)
        # Round up to nearest integer for discrete ordering
        order_amount = int(order_amount + 0.5)
    else:
        order_amount = 0

    # Apply minimum order threshold
    if order_amount < min_order_threshold:
        order_amount = 0

    return order_amount
