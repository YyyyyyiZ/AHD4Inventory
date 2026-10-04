# policy_hash: 1c56556138e55d8d7df0d113975d1ace31f5ed815b35c76b12da7e0b902168e7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 46
# source_prompt_files: 2
# best_target_performance: 10253.76
# best_prompt_performance: 10253.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_072107.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 295.2634566607504  # OPT_PARAM: {"initial": 295.2634566607504, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 20.332206660755958  # OPT_PARAM: {"initial": 20.332206660755958, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline arrivals
    # Use average of last 2 arriving orders as demand proxy
    recent_arrivals = []
    if len(pipeline_orders) >= 2:
        recent_arrivals = pipeline_orders[:2]
    elif len(pipeline_orders) > 0:
        recent_arrivals = pipeline_orders[:1]

    forecast_demand = 0
    if recent_arrivals:
        forecast_demand = sum(recent_arrivals) / len(recent_arrivals) * demand_forecast_factor

    # Adjust base stock based on forecast
    adjusted_base_stock = base_stock + forecast_demand

    # Calculate target inventory position
    target_position = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Round to nearest integer since order amount should be int
    return order_amount
