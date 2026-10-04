# policy_hash: 010e6b2055be94b979857dcb785f85e515b4e38fa8429bba3faf198613e064e8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 2
# best_target_performance: 2949.48
# best_prompt_performance: 2948.03
# best_rel_error_pct: 0.049161
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_054434.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 821.6243548573843  # OPT_PARAM: {"initial": 821.6243548573843, "min": 700, "max": 1000, "type": "float"}
    safety_stock = 146.61689972113751  # OPT_PARAM: {"initial": 146.61689972113751, "min": 100, "max": 250, "type": "float"}
    smoothing_factor = 0.3574386365413122  # OPT_PARAM: {"initial": 0.3574386365413122, "min": 0.3, "max": 0.8, "type": "float"}
    demand_forecast_factor = 0.8417528282026991  # OPT_PARAM: {"initial": 0.8417528282026991, "min": 0.7, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    recent_arrivals = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 100.0

    # Adjust target based on demand forecast
    adjusted_base = base_stock * demand_forecast_factor

    # Calculate target inventory level
    target_inventory = adjusted_base + safety_stock

    # Calculate order gap with demand consideration
    order_gap = target_inventory - inventory_position

    # Add demand forecast to order to better match upcoming needs
    demand_adjusted_gap = order_gap + avg_recent_demand * 0.3

    # Smooth ordering with stronger response to shortages
    if demand_adjusted_gap > 0:
        order_amount = smoothing_factor * demand_adjusted_gap
    else:
        # More aggressive response when inventory is too high
        order_amount = 0.2 * demand_adjusted_gap if demand_adjusted_gap < -50 else 0

    # Ensure non-negative order
    order_amount = max(0, order_amount)

    # Round to nearest integer
    return order_amount
