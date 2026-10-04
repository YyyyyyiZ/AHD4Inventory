# policy_hash: afb92619ca012f9a36220257d35c1bebacd6ed24fdf986f2b798acbf77bb7a37
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 6400.22
# best_prompt_performance: 6394.72
# best_rel_error_pct: 0.085935
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223014.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 223.9069894407264  # OPT_PARAM: {"initial": 223.9069894407264, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 65.96063538275246  # OPT_PARAM: {"initial": 65.96063538275246, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    if len(pipeline_orders) > 0:
        recent_arrivals = [p for p in pipeline_orders if p > 0]
        if recent_arrivals:
            avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
        else:
            avg_recent_demand = 0
    else:
        avg_recent_demand = 0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand

    # Calculate target inventory position
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_recent_demand

    # Round to nearest integer (as required by problem statement)
    order_amount = int(round(order_amount))

    return order_amount
