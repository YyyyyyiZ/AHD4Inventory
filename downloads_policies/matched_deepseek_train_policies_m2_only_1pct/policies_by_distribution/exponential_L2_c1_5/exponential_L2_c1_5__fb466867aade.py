# policy_hash: fb466867aadec4a448794ce62d1bc7570f7a4087d9e59b0ae41844af221e40a9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 26
# source_prompt_files: 1
# best_target_performance: 10550.8
# best_prompt_performance: 10550.06
# best_rel_error_pct: 0.007014
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_072518.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 375.44141941310346  # OPT_PARAM: {"initial": 375.44141941310346, "min": 100, "max": 800, "type": "float"}
    safety_stock = 20.452131408036713  # OPT_PARAM: {"initial": 20.452131408036713, "min": 0, "max": 100, "type": "float"}
    demand_forecast_factor = 0.7656461829588668  # OPT_PARAM: {"initial": 0.7656461829588668, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using recent pipeline arrivals
    if len(pipeline_orders) >= 2:
        recent_arrivals = pipeline_orders[:2]
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = base_stock / 8

    # Adjust base stock dynamically based on demand forecast
    adjusted_base_stock = base_stock * demand_forecast_factor + safety_stock

    # Calculate target order with threshold to avoid small orders
    target_order = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothing_factor = 0.6200579180118373  # OPT_PARAM: {"initial": 0.6200579180118373, "min": 0.3, "max": 0.9, "type": "float"}
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * target_order + (1 - smoothing_factor) * last_order
    else:
        smoothed_order = target_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    # Cap order amount to prevent excessive ordering
    max_order = 800  # OPT_PARAM: {"initial": 800, "min": 300, "max": 1500, "type": "int"}
    order_amount = min(order_amount, max_order)

    # Minimum order threshold to reduce small orders
    min_order = 20  # OPT_PARAM: {"initial": 20, "min": 0, "max": 100, "type": "int"}
    if order_amount < min_order:
        order_amount = 0

    return order_amount
