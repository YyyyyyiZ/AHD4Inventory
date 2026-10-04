# policy_hash: be0337af0d221099442cb947e32da28cd0d8dbd7d0485278edac26a77e4961fe
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 11030.34
# best_prompt_performance: 11030.34
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_050834.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 418.28067133161346  # OPT_PARAM: {"initial": 418.28067133161346, "min": 300, "max": 700, "type": "float"}
    safety_stock = 118.28067133161298  # OPT_PARAM: {"initial": 118.28067133161298, "min": 50, "max": 250, "type": "float"}
    demand_forecast_factor = 1.1358621075215782  # OPT_PARAM: {"initial": 1.1358621075215782, "min": 0.5, "max": 1.5, "type": "float"}
    smoothing_factor = 0.16700171878671877  # OPT_PARAM: {"initial": 0.16700171878671877, "min": 0.1, "max": 0.8, "type": "float"}
    order_threshold = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 10, "max": 100, "type": "float"}
    lead_time_demand_factor = 3.2190815886419712  # OPT_PARAM: {"initial": 3.2190815886419712, "min": 1.5, "max": 4.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast using average of recent pipeline orders
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        forecast_demand = avg_pipeline * demand_forecast_factor * lead_time_demand_factor
    else:
        forecast_demand = 0

    # Dynamic base stock adjustment
    adjusted_base_stock = base_stock + safety_stock + forecast_demand

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing only for larger orders
    if order_amount > order_threshold:
        order_amount = smoothing_factor * order_amount

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
