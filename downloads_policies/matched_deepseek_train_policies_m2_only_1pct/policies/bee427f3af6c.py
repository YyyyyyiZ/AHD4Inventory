# policy_hash: bee427f3af6c9da04722b4e64f19a3e775df79f4a09af451bcf121f785ef2b34
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 21
# source_prompt_files: 1
# best_target_performance: 6273.0
# best_prompt_performance: 6273.0
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_035751.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 277.3780586664066  # OPT_PARAM: {"initial": 277.3780586664066, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 29.857883986382156  # OPT_PARAM: {"initial": 29.857883986382156, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 2.0, "type": "float"}
    pipeline_weight = 0.20529014649501406  # OPT_PARAM: {"initial": 0.20529014649501406, "min": 0.0, "max": 1.0, "type": "float"}
    inventory_weight = 0.08803912263659276  # OPT_PARAM: {"initial": 0.08803912263659276, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate adjusted base stock level
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order-up-to level with adjustment
    order_up_to = adjusted_base_stock - effective_inventory

    # Apply smoothing to avoid large order fluctuations
    if order_up_to > 0:
        # Weight current inventory position more heavily
        smoothed_order = (inventory_weight * order_up_to +
                         pipeline_weight * max(0, base_stock - on_hand_inventory))
        order_amount = max(0, smoothed_order)
    else:
        order_amount = 0

    # Round to nearest integer (as required by problem)
    return order_amount
