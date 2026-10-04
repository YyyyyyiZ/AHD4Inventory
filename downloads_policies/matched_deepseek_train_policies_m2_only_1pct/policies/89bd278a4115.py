# policy_hash: 89bd278a4115741defe2c87fe9e8e7c687678bc2ded100c5ce8164e571abd4ab
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 7318.22
# best_prompt_performance: 7318.22
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_091316.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 323.556395039516  # OPT_PARAM: {"initial": 323.556395039516, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 16.59623759687655  # OPT_PARAM: {"initial": 16.59623759687655, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline orders (as proxy for recent demand)
    # Use average of recent orders as demand forecast
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
        forecast_demand = sum(recent_orders) / len(recent_orders) * demand_forecast_factor
    else:
        forecast_demand = 0

    # Adjust base stock level based on forecast
    adjusted_base_stock = base_stock + forecast_demand + safety_stock

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Round to nearest integer since order amounts should be integers
    return order_amount
