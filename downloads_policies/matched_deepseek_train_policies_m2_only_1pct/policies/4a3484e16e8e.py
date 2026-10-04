# policy_hash: 4a3484e16e8ed631cf27906eb4998a3dac10afe1a453e0e2fd2068120de90c1e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 978.23
# best_prompt_performance: 978.22
# best_rel_error_pct: 0.001022
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_022135.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 294.0000013139217  # OPT_PARAM: {"initial": 294.0000013139217, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 200.0  # OPT_PARAM: {"initial": 200.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 93.95202433796526  # OPT_PARAM: {"initial": 93.95202433796526, "min": 50, "max": 150, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline status
    pipeline_ratio = sum(pipeline_orders) / (len(pipeline_orders) * demand_forecast) if len(pipeline_orders) > 0 else 1.0
    adjusted_base_stock = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base_stock, demand_forecast + safety_stock)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid large order fluctuations
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    if order_amount > 2 * demand_forecast:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * 2 * demand_forecast

    return order_amount
