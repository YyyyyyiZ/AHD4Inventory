# policy_hash: 93750f864aa7a70d65b21956b269635c4232b995006d8d8a53ff07cfea078ca1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 3780.18
# best_prompt_performance: 3780.54
# best_rel_error_pct: 0.009523
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_080631.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 819.9439255026144  # OPT_PARAM: {"initial": 819.9439255026144, "min": 400, "max": 900, "type": "float"}
    safety_factor = 2.9999744791998  # OPT_PARAM: {"initial": 2.9999744791998, "min": 1.0, "max": 3.0, "type": "float"}
    demand_forecast_window = 10  # OPT_PARAM: {"initial": 10, "min": 5, "max": 20, "type": "int"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand based on recent pipeline arrivals
    # Use pipeline orders as proxy for recent demand (since they were placed L periods ago)
    recent_orders = pipeline_orders[-min(demand_forecast_window, len(pipeline_orders)):]
    if recent_orders:
        avg_recent_demand = sum(recent_orders) / len(recent_orders)
    else:
        avg_recent_demand = base_stock / 6  # fallback

    # Dynamic safety stock based on demand variability
    if len(recent_orders) > 1:
        demand_variance = sum((x - avg_recent_demand) ** 2 for x in recent_orders) / len(recent_orders)
        safety_stock = safety_factor * (demand_variance ** 0.5)
    else:
        safety_stock = safety_factor * avg_recent_demand * 0.5

    # Adjust base stock based on demand pattern
    adjusted_base = base_stock * (avg_recent_demand / (base_stock / 6))
    adjusted_base = max(base_stock * 0.7, min(base_stock * 1.3, adjusted_base))

    # Target inventory position
    target_inventory = adjusted_base + safety_stock

    # Calculate order with smoothing
    desired_order = max(0, target_inventory - inventory_position)
    order_amount = smoothing_factor * desired_order + (1 - smoothing_factor) * avg_recent_demand

    # Ensure integer order amount
    return order_amount
