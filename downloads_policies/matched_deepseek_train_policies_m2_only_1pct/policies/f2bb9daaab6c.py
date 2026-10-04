# policy_hash: f2bb9daaab6c65ed5930913257a6b675d055436f40113095a7b6c5efa5dfbc97
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 6161.04
# best_prompt_performance: 6161.04
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_040817.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 324.9376920159711  # OPT_PARAM: {"initial": 324.9376920159711, "min": 200, "max": 600, "type": "float"}
    demand_window = 5  # OPT_PARAM: {"initial": 5, "min": 1, "max": 10, "type": "int"}
    safety_factor = 1.5965523694436934  # OPT_PARAM: {"initial": 1.5965523694436934, "min": 1.0, "max": 3.0, "type": "float"}
    smoothing_factor = 0.1785824921896045  # OPT_PARAM: {"initial": 0.1785824921896045, "min": 0.1, "max": 1.0, "type": "float"}
    pipeline_weight = 0.4343018527538215  # OPT_PARAM: {"initial": 0.4343018527538215, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use pipeline arrivals as demand proxy (they reflect past actual demands)
    if len(pipeline_orders) >= demand_window:
        recent_arrivals = pipeline_orders[:demand_window]
    else:
        recent_arrivals = pipeline_orders if pipeline_orders else [0]

    # Calculate demand forecast using weighted average
    # Give more weight to recent arrivals
    weights = [0.5 ** i for i in range(len(recent_arrivals))]
    weights = [w/sum(weights) for w in weights]
    weighted_forecast = sum(r * w for r, w in zip(recent_arrivals, weights))

    # Calculate safety stock based on demand variability
    if len(recent_arrivals) >= 2:
        avg_demand = sum(recent_arrivals) / len(recent_arrivals)
        demand_variance = sum((r - avg_demand) ** 2 for r in recent_arrivals) / len(recent_arrivals)
        safety_stock = safety_factor * (demand_variance ** 0.5)
    else:
        safety_stock = safety_factor * (weighted_forecast * 0.5)

    # Adjust base stock with safety stock
    adjusted_base_stock = base_stock + safety_stock

    # Consider pipeline content in target calculation
    # If pipeline is large, reduce target to avoid overstocking
    pipeline_content = sum(pipeline_orders)
    pipeline_adjustment = pipeline_weight * pipeline_content

    # Calculate target inventory position
    target_inventory_position = adjusted_base_stock + weighted_forecast - pipeline_adjustment

    # Calculate order needed
    order_needed = target_inventory_position - inventory_position

    # Apply smoothing with forecast consideration
    if order_needed > 0:
        smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * weighted_forecast
    else:
        smoothed_order = smoothing_factor * order_needed

    # Round and ensure non-negative
    order_amount = int(round(max(0, smoothed_order)))

    return order_amount
