# policy_hash: b1216e9a8766287ec6b872bd9052b983450e4afa3093a13208685b31302cf2fa
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 11186.14
# best_prompt_performance: 11186.14
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031159.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 324.9312499999593  # OPT_PARAM: {"initial": 324.9312499999593, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 49.99999999997124  # OPT_PARAM: {"initial": 49.99999999997124, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline arrivals
    # Use average of last L periods of actual arrivals as proxy for demand
    recent_arrivals = pipeline_orders[:2]  # L=2
    if len(recent_arrivals) > 0:
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
        forecast_demand = avg_recent_demand * demand_forecast_factor
    else:
        forecast_demand = 0

    # Adjust base stock level based on forecast
    adjusted_base_stock = base_stock + safety_stock + forecast_demand

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Round to nearest integer since order amount should be integer
    order_amount = int(round(order_amount))

    return order_amount
