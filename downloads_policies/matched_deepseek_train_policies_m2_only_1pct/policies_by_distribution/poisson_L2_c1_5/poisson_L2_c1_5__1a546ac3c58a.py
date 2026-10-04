# policy_hash: 1a546ac3c58a2afeec5b582029ef9b49bb312cb58b7c8153454205ccb35d6075
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 1232.88
# best_prompt_performance: 1232.88
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031756.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 274.50339956961324  # OPT_PARAM: {"initial": 274.50339956961324, "min": 250, "max": 320, "type": "float"}
    safety_stock = 15.828135243907056  # OPT_PARAM: {"initial": 15.828135243907056, "min": 10, "max": 30, "type": "float"}
    demand_estimate = 98.37626902969052  # OPT_PARAM: {"initial": 98.37626902969052, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.28646375246616296  # OPT_PARAM: {"initial": 0.28646375246616296, "min": 0.2, "max": 0.6, "type": "float"}
    smoothing_factor = 0.11797920494582743  # OPT_PARAM: {"initial": 0.11797920494582743, "min": 0.02, "max": 0.15, "type": "float"}
    lost_sales_weight = 1.6131054380483052  # OPT_PARAM: {"initial": 1.6131054380483052, "min": 1.2, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with lost-sales adjustment
    target_level = base_stock + safety_stock * lost_sales_weight

    # Base order amount
    base_order = max(0, target_level - inventory_position)

    # Add pipeline-aware adjustment
    if len(pipeline_orders) > 0:
        expected_pipeline = demand_estimate * len(pipeline_orders)
        current_pipeline = sum(pipeline_orders)
        pipeline_deficit = max(0, expected_pipeline - current_pipeline)
        base_order += pipeline_weight * pipeline_deficit

    # Apply smoothing with stronger demand anchoring
    order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_estimate

    # Ensure non-negative integer order
    order_amount = max(0, int(round(order_amount)))

    return order_amount
