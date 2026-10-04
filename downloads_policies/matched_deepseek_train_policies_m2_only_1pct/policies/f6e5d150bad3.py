# policy_hash: f6e5d150bad30a92001d93ae99642973f4270793d554e26285f15c1e01ccd55a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 20
# source_prompt_files: 1
# best_target_performance: 11100.96
# best_prompt_performance: 11100.96
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_044943.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 382.4160762793782  # OPT_PARAM: {"initial": 382.4160762793782, "min": 200, "max": 600, "type": "float"}
    safety_stock = 87.11607627938034  # OPT_PARAM: {"initial": 87.11607627938034, "min": 20, "max": 200, "type": "float"}
    demand_forecast_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.3, "max": 1.2, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    lead_time_demand_factor = 3.0  # OPT_PARAM: {"initial": 3.0, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate lead time demand using pipeline orders as proxy
    if len(pipeline_orders) > 0:
        # Use weighted average with more weight on recent orders
        weights = [0.3, 0.25, 0.2, 0.15] if len(pipeline_orders) >= 4 else [1.0/len(pipeline_orders)] * len(pipeline_orders)
        weighted_sum = sum(w * q for w, q in zip(weights[:len(pipeline_orders)], pipeline_orders))
        weight_sum = sum(weights[:len(pipeline_orders)])
        avg_lead_time_demand = weighted_sum / weight_sum if weight_sum > 0 else 0
        forecast_demand = avg_lead_time_demand * demand_forecast_factor * lead_time_demand_factor
    else:
        forecast_demand = 0

    # Dynamic base stock adjustment
    adjusted_base_stock = base_stock + safety_stock + forecast_demand

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing with threshold
    if order_amount > 50:  # Only smooth larger orders
        order_amount = smoothing_factor * order_amount

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
