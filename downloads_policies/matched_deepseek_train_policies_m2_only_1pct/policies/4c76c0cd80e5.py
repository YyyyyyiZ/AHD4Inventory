# policy_hash: 4c76c0cd80e5b35a19a2b8444c0647d28d29de72c6322aff0a59c534df3b0f06
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 5421.2
# best_prompt_performance: 5424.63
# best_rel_error_pct: 0.063270
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_172643.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 455.6780981521265  # OPT_PARAM: {"initial": 455.6780981521265, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 21.7259280102189  # OPT_PARAM: {"initial": 21.7259280102189, "min": 0, "max": 300, "type": "float"}
    demand_forecast_factor = 0.5167866863182633  # OPT_PARAM: {"initial": 0.5167866863182633, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline arrivals
    # Use average of last 3 arriving orders as demand proxy
    recent_arrivals = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand

    # Calculate target inventory position
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    return order_amount
