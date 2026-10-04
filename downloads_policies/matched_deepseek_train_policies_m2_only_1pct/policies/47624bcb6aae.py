# policy_hash: 47624bcb6aae92ee8d20c5f98f634c74b9b2ce1a28912207c09cd46e8f81635e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 2127.94
# best_prompt_performance: 2127.34
# best_rel_error_pct: 0.028196
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_044144.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 482.72985622467587  # OPT_PARAM: {"initial": 482.72985622467587, "min": 300, "max": 600, "type": "float"}
    safety_stock = 37.72985622467639  # OPT_PARAM: {"initial": 37.72985622467639, "min": 0, "max": 100, "type": "float"}
    demand_forecast_factor = 1.056860867669777  # OPT_PARAM: {"initial": 1.056860867669777, "min": 0.8, "max": 1.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with demand forecasting
    # Use average of recent pipeline arrivals as demand estimate
    if len(pipeline_orders) >= 2:
        recent_arrivals = pipeline_orders[-2:]  # Last two pipeline orders
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
        forecast_adjustment = avg_recent_demand * (demand_forecast_factor - 1.0)
    else:
        forecast_adjustment = 0

    target_inventory = base_stock + safety_stock + forecast_adjustment

    # Calculate order quantity
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing with threshold to avoid small orders
    smoothing_factor = 0.7693390451709179  # OPT_PARAM: {"initial": 0.7693390451709179, "min": 0.5, "max": 1.0, "type": "float"}
    min_order_threshold = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 50, "type": "float"}

    if order_amount > min_order_threshold:
        order_amount = smoothing_factor * order_amount
    elif order_amount > 0:
        order_amount = 0  # Skip very small orders

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
