# policy_hash: f58823d7b7cd6f26818fe3c6470c18872b47ff71ddf1018d3b897eadc3431011
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 6282.75
# best_prompt_performance: 6282.95
# best_rel_error_pct: 0.003183
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223243.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 194.1502947716094  # OPT_PARAM: {"initial": 194.1502947716094, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 36.20394071363242  # OPT_PARAM: {"initial": 36.20394071363242, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    recent_arrivals = [p for p in pipeline_orders if p > 0]
    if recent_arrivals:
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = base_stock / 4  # Fallback estimate

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * (avg_recent_demand - base_stock/4)

    # Add safety stock for variability
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer (since order amount should be integer)
    order_amount = int(round(order_amount))

    return order_amount
