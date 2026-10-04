# policy_hash: b5d48b672a1453e5a510e919f29b4410927af972821730ee7afcfe46afd6dcdb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 11026.74
# best_prompt_performance: 11025.94
# best_rel_error_pct: 0.007255
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031625.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 225.0967200423734  # OPT_PARAM: {"initial": 225.0967200423734, "min": 100, "max": 600, "type": "float"}
    safety_stock = 20.307668675575655  # OPT_PARAM: {"initial": 20.307668675575655, "min": 20, "max": 150, "type": "float"}
    demand_smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.9, "type": "float"}
    pipeline_weight = 0.7824921735492492  # OPT_PARAM: {"initial": 0.7824921735492492, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from pipeline arrivals (more stable than historical policy)
    # Weight recent arrivals more heavily
    if len(pipeline_orders) >= 2:
        # Weighted average: recent arrival gets more weight
        weighted_demand = (pipeline_orders[0] * 0.6 + pipeline_orders[1] * 0.4) if len(pipeline_orders) == 2 else pipeline_orders[0]
        # Smooth with previous estimate
        forecast_demand = weighted_demand * demand_smoothing
    else:
        forecast_demand = 0

    # Adjust base stock dynamically based on pipeline status
    # If pipeline is low, increase target; if high, decrease
    pipeline_total = sum(pipeline_orders)
    pipeline_adjustment = (base_stock * 0.5 - pipeline_total) * pipeline_weight

    # Calculate target inventory position
    target_position = base_stock + safety_stock + forecast_demand + pipeline_adjustment

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply rounding with threshold to avoid tiny orders
    if order_amount < 5.0:
        order_amount = 0
    else:
        order_amount = int(round(order_amount))

    return order_amount
