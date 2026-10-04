# policy_hash: 3f67c07d9117bb3712833b2682c4391ca4bac8c46e69b1f99723bb8c27f6234b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 11698.28
# best_prompt_performance: 11704.79
# best_rel_error_pct: 0.055649
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_022534.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 363.8908918822749  # OPT_PARAM: {"initial": 363.8908918822749, "min": 300, "max": 450, "type": "float"}
    pipeline_weight = 0.9903205498598399  # OPT_PARAM: {"initial": 0.9903205498598399, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.08047599274670658  # OPT_PARAM: {"initial": 0.08047599274670658, "min": 0.05, "max": 0.3, "type": "float"}
    safety_stock = 73.89089188226963  # OPT_PARAM: {"initial": 73.89089188226963, "min": 60, "max": 150, "type": "float"}
    demand_buffer = 1.0963036443258085  # OPT_PARAM: {"initial": 1.0963036443258085, "min": 1.0, "max": 1.4, "type": "float"}
    min_order = 15.12629637551136  # OPT_PARAM: {"initial": 15.12629637551136, "min": 0, "max": 30, "type": "float"}
    max_order = 450.0  # OPT_PARAM: {"initial": 450.0, "min": 350, "max": 550, "type": "float"}
    recent_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.5, "max": 0.9, "type": "float"}
    lost_sales_weight = 1.172537679390752  # OPT_PARAM: {"initial": 1.172537679390752, "min": 1.0, "max": 1.8, "type": "float"}
    pipeline_lookback = 3  # OPT_PARAM: {"initial": 3, "min": 2, "max": 5, "type": "int"}

    # Calculate total pipeline
    total_pipeline = sum(pipeline_orders)

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = total_pipeline * pipeline_weight
    inventory_position = on_hand_inventory + weighted_pipeline

    # Estimate expected demand from recent pipeline arrivals
    if len(pipeline_orders) >= pipeline_lookback:
        recent_orders = pipeline_orders[:pipeline_lookback]
        avg_recent_demand = sum(recent_orders) / len(recent_orders)

        # Use slightly older orders as baseline if available
        if len(pipeline_orders) >= 6:
            older_orders = pipeline_orders[3:6]
            avg_older_demand = sum(older_orders) / len(older_orders)
            expected_demand = (recent_weight * avg_recent_demand +
                             (1 - recent_weight) * avg_older_demand) * demand_buffer
        else:
            expected_demand = avg_recent_demand * demand_buffer
    else:
        expected_demand = 0

    # Dynamic base stock adjustment
    adjusted_base_stock = base_stock + safety_stock + (expected_demand * lost_sales_weight)

    # Base-stock policy calculation
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing with recent order patterns
    if len(pipeline_orders) >= 2:
        avg_recent = sum(pipeline_orders[-2:]) / 2
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_recent

    # Apply order limits
    order_amount = max(min_order, min(max_order, order_amount))

    # Round to nearest integer
    return order_amount
