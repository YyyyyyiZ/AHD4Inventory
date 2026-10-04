# policy_hash: bb8198fb8607e14dca4a7cdb3a74569d5b62ccad8c1522b123702186299a1afc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 13
# source_prompt_files: 2
# best_target_performance: 11391.4
# best_prompt_performance: 11391.4
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_004304.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 387.7999610841117  # OPT_PARAM: {"initial": 387.7999610841117, "min": 200, "max": 600, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 50, "max": 250, "type": "float"}
    demand_forecast_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 2.0, "type": "float"}
    smoothing_factor = 0.09542450340381547  # OPT_PARAM: {"initial": 0.09542450340381547, "min": 0.0, "max": 0.5, "type": "float"}
    lead_time = 4  # OPT_PARAM: {"initial": 4, "min": 1, "max": 8, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate future demand using exponential smoothing of recent pipeline arrivals
    if pipeline_orders:
        # Use weighted average with more weight on recent orders
        weights = [0.1, 0.2, 0.3, 0.4][:len(pipeline_orders)]
        weights = [w/sum(weights) for w in weights]
        avg_recent_demand = sum(w * d for w, d in zip(weights, pipeline_orders))
    else:
        avg_recent_demand = 0

    # Forecast lead time demand
    forecast_demand = avg_recent_demand * demand_forecast_factor * lead_time

    # Calculate order-up-to level
    order_up_to = max(base_stock, safety_stock + forecast_demand)

    # Place order to reach order-up-to level
    order_amount = max(0, order_up_to - inventory_position)

    # Apply moderate smoothing to prevent extreme fluctuations
    if pipeline_orders and len(pipeline_orders) >= 2:
        last_order = pipeline_orders[-1]
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * last_order

    # Round to nearest integer (since order amount must be integer)
    order_amount = int(round(order_amount))

    return order_amount
