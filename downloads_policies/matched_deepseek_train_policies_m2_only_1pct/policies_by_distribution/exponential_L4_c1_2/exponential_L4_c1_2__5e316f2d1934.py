# policy_hash: 5e316f2d1934920bae87983d9c9eeaa8f042d5a351398598d4367c8581347c74
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 7018.06
# best_prompt_performance: 7018.06
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_234709.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 282.9634550835291  # OPT_PARAM: {"initial": 282.9634550835291, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    if len(pipeline_orders) >= 2:
        recent_arrivals = pipeline_orders[-2:]  # Last two pipeline orders
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = 0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand

    # Calculate order-up-to level
    order_up_to = max(adjusted_base_stock, safety_stock)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Smooth ordering by limiting maximum order size
    max_order = 400.0  # OPT_PARAM: {"initial": 400.0, "min": 100, "max": 800, "type": "float"}
    order_amount = min(order_amount, max_order)

    # Ensure integer order amount
    order_amount = int(round(order_amount))

    return order_amount
