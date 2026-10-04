# policy_hash: 6dac791c23eeefd34145b4aaede6aa3de7bdc37ac5a0841d4713adaec1d87552
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 2
# best_target_performance: 2938.48
# best_prompt_performance: 2944.87
# best_rel_error_pct: 0.217459
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_055020.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 693.8857285351294  # OPT_PARAM: {"initial": 693.8857285351294, "min": 500, "max": 1200, "type": "float"}
    safety_stock = 93.88572853510557  # OPT_PARAM: {"initial": 93.88572853510557, "min": 50, "max": 300, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    lead_time = 6  # OPT_PARAM: {"initial": 6, "min": 1, "max": 10, "type": "int"}
    demand_forecast_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Forecast demand based on recent pipeline orders (proxy for recent demand)
    recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent_demand = sum(recent_orders) / max(len(recent_orders), 1)
    forecast_adjustment = avg_recent_demand * demand_forecast_factor * lead_time

    # Dynamic target inventory with forecast adjustment
    target_inventory = base_stock + safety_stock + forecast_adjustment

    # Calculate order needed to reach target
    order_needed = target_inventory - inventory_position

    # Apply smoothing with minimum order threshold
    if order_needed > 0:
        order_amount = max(0, smoothing_factor * order_needed)
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
