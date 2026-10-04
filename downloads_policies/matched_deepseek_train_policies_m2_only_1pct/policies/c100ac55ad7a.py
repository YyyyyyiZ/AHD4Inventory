# policy_hash: c100ac55ad7aeac7b3220245db874b8abe237c3b84403221d469ba49b694c7b6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 10800.0
# best_prompt_performance: 10798.92
# best_rel_error_pct: 0.010000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031601.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 324.93124999998804  # OPT_PARAM: {"initial": 324.93124999998804, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.17399325446453165  # OPT_PARAM: {"initial": 0.17399325446453165, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline arrivals
    # Use average of last 2 arriving orders as demand proxy
    if len(pipeline_orders) >= 2 and pipeline_orders[0] > 0:
        recent_demand_estimate = (pipeline_orders[0] + pipeline_orders[1]) / 2
    else:
        recent_demand_estimate = base_stock * 0.3

    # Adjust base stock based on recent demand
    adjusted_base_stock = base_stock * (1 + demand_forecast_factor * (recent_demand_estimate / base_stock - 1))

    # Calculate order amount with safety stock buffer
    order_amount = max(0, adjusted_base_stock + safety_stock - inventory_position)

    # Round to nearest integer since order amount should be integer
    order_amount = int(round(order_amount))

    return order_amount
