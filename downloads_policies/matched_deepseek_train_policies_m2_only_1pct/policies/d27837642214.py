# policy_hash: d2783764221451313dee23922614aced2987a8975e68c46c83a3a0b4232ee69c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 11119.4
# best_prompt_performance: 11117.84
# best_rel_error_pct: 0.014030
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_044927.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 447.7315242666826  # OPT_PARAM: {"initial": 447.7315242666826, "min": 300, "max": 700, "type": "float"}
    safety_stock = 77.731524266682  # OPT_PARAM: {"initial": 77.731524266682, "min": 30, "max": 150, "type": "float"}
    order_smoothing = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.9, "type": "float"}
    demand_forecast_factor = 0.7025867295166407  # OPT_PARAM: {"initial": 0.7025867295166407, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_weight = 0.5894451330657767  # OPT_PARAM: {"initial": 0.5894451330657767, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast using pipeline arrivals (recent actual deliveries)
    if len(pipeline_orders) > 0 and pipeline_orders[0] > 0:
        # Use most recent arrival as demand indicator
        recent_demand_indicator = pipeline_orders[0] * demand_forecast_factor
    else:
        recent_demand_indicator = 0

    # Adjust base stock based on recent demand
    adjusted_base = base_stock + recent_demand_indicator * pipeline_weight

    # Target inventory level
    target_inventory = adjusted_base + safety_stock

    # Calculate order needed
    order_needed = max(0, target_inventory - inventory_position)

    # Apply order smoothing
    if order_needed > 0:
        order_amount = order_needed * order_smoothing
    else:
        order_amount = 0

    # Ensure minimum practical order
    if 0 < order_amount < 10:
        order_amount = 10

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
