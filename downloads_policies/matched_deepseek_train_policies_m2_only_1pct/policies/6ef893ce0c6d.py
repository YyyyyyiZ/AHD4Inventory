# policy_hash: 6ef893ce0c6d3137ff8ce68838446e1ffcc168a57bd3f36bed7726d8b4362697
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 40
# source_prompt_files: 1
# best_target_performance: 1276.24
# best_prompt_performance: 1276.24
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_231932.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 306.3589518841922  # OPT_PARAM: {"initial": 306.3589518841922, "min": 250, "max": 380, "type": "float"}
    safety_stock = 27.250717418087717  # OPT_PARAM: {"initial": 27.250717418087717, "min": 20, "max": 60, "type": "float"}
    pipeline_weight = 0.95  # OPT_PARAM: {"initial": 0.95, "min": 0.7, "max": 1.1, "type": "float"}
    adjustment_factor = 0.791976588922788  # OPT_PARAM: {"initial": 0.791976588922788, "min": 0.7, "max": 1.1, "type": "float"}
    demand_buffer = 0.9919765889227881  # OPT_PARAM: {"initial": 0.9919765889227881, "min": 0.9, "max": 1.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective base stock with demand buffer
    effective_base = base_stock * demand_buffer

    # Calculate weighted pipeline for lead time demand estimation
    if len(pipeline_orders) > 0:
        weighted_pipeline = 0
        total_weight = 0
        for i, order in enumerate(pipeline_orders):
            # Exponential weighting: newer orders get higher weight
            weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
            weighted_pipeline += order * weight
            total_weight += weight

        avg_weighted_pipeline = weighted_pipeline / total_weight if total_weight > 0 else 0

        # Adjust target based on pipeline and safety stock
        pipeline_adjustment = max(0, avg_weighted_pipeline - base_stock * 0.5)
        target_inventory = effective_base + safety_stock - pipeline_adjustment
    else:
        target_inventory = effective_base + safety_stock

    # Calculate order amount with smoother adjustment
    raw_order = max(0, target_inventory - inventory_position)

    # Apply adjustment factor with rounding to nearest integer
    order_amount = int(round(raw_order * adjustment_factor))

    return order_amount
