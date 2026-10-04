# policy_hash: a6ca3c8752b946ae11797e77c83ddc68482a1cc906a5016f9deedc76302002ae
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 5426.32
# best_prompt_performance: 5425.78
# best_rel_error_pct: 0.009951
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_225610.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 482.25223330665176  # OPT_PARAM: {"initial": 482.25223330665176, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 2.193060678123276  # OPT_PARAM: {"initial": 2.193060678123276, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.48462935040560773  # OPT_PARAM: {"initial": 0.48462935040560773, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline arrivals
    # Use average of last 3 arriving orders as demand proxy
    recent_arrivals = pipeline_orders[:3]
    if len(recent_arrivals) > 0:
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = 0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand

    # Calculate target inventory position
    target_position = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Round to nearest integer since order amount should be integer
    return order_amount
