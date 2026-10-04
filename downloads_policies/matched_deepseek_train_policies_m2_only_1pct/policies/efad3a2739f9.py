# policy_hash: efad3a2739f9861354579a79270f5579eaa6904157dcb8961a80bce3971d4fa9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 11296.33
# best_prompt_performance: 11296.33
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_003333.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 448.9479628545371  # OPT_PARAM: {"initial": 448.9479628545371, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 150.06533162100072  # OPT_PARAM: {"initial": 150.06533162100072, "min": 50, "max": 400, "type": "float"}
    demand_forecast_factor = 0.7317720397989579  # OPT_PARAM: {"initial": 0.7317720397989579, "min": 0.1, "max": 2.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate future demand based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:2] if len(pipeline_orders) >= 2 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock dynamically based on demand pattern
    adjusted_base_stock = base_stock * (1 + smoothing_factor * (avg_recent_demand * demand_forecast_factor / base_stock - 1))

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base_stock, safety_stock + avg_recent_demand * demand_forecast_factor * 4)

    # Place order to reach order-up-to level
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    if pipeline_orders:
        last_order = pipeline_orders[-1]
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * last_order

    return order_amount
