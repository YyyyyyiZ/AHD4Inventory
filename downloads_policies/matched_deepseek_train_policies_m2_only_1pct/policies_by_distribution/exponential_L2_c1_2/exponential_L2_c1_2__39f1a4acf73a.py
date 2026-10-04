# policy_hash: 39f1a4acf73a3856607ef029a4fa597509e273bb6b64ecdc6813c32908bd1a53
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 5983.22
# best_prompt_performance: 5982.43
# best_rel_error_pct: 0.013204
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_104703.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 165.07068885656284  # OPT_PARAM: {"initial": 165.07068885656284, "min": 50, "max": 400, "type": "float"}
    safety_stock = 30.0  # OPT_PARAM: {"initial": 30.0, "min": 10, "max": 100, "type": "float"}
    demand_forecast_factor = 0.36709454976829886  # OPT_PARAM: {"initial": 0.36709454976829886, "min": 0.1, "max": 2.0, "type": "float"}
    smoothing_factor = 0.24427554780316543  # OPT_PARAM: {"initial": 0.24427554780316543, "min": 0.1, "max": 0.8, "type": "float"}
    pipeline_weight = 0.2766832683015596  # OPT_PARAM: {"initial": 0.2766832683015596, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of pipeline orders
    if len(pipeline_orders) > 0:
        # Simple average of pipeline orders (recent shipments reflect recent demand)
        forecast_demand = sum(pipeline_orders) / len(pipeline_orders)
    else:
        forecast_demand = 0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * forecast_demand

    # Incorporate pipeline information more directly
    pipeline_effect = pipeline_weight * sum(pipeline_orders)
    order_up_to = max(adjusted_base_stock + pipeline_effect, safety_stock)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing using recent pipeline orders
    if len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * recent_order
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to nearest integer
    return order_amount
