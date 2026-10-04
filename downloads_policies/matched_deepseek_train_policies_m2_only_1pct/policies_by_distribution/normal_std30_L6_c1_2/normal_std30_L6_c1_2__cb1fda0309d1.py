# policy_hash: cb1fda0309d12e39b6976c21782171dcb55e11f8038a58b368a1a4929e0555ae
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 18
# source_prompt_files: 1
# best_target_performance: 2859.22
# best_prompt_performance: 2859.22
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_014917.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 605.9671878193278  # OPT_PARAM: {"initial": 605.9671878193278, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    recent_arrivals = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / max(len(recent_arrivals), 1)

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * (avg_recent_demand - 100)

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base_stock, safety_stock)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * last_order
        order_amount = max(0, smoothed_order)

    return order_amount
