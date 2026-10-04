# policy_hash: ffa5072b67339df064f56202a60a5e10e86776d25785dad84588008f1ab54ca6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 6038.36
# best_prompt_performance: 6038.36
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_034456.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 271.2769109892467  # OPT_PARAM: {"initial": 271.2769109892467, "min": 100, "max": 500, "type": "float"}
    pipeline_weight = 1.007286624916035  # OPT_PARAM: {"initial": 1.007286624916035, "min": 0.5, "max": 1.2, "type": "float"}
    demand_buffer = 1.5325151981851117  # OPT_PARAM: {"initial": 1.5325151981851117, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate order-up-to level with demand buffer
    order_up_to = base_stock * demand_buffer

    # Base order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply aggressive smoothing based on pipeline variability
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        smoothing_factor = 0.11599514127181858  # OPT_PARAM: {"initial": 0.11599514127181858, "min": 0.1, "max": 0.5, "type": "float"}
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_pipeline
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    return order_amount
