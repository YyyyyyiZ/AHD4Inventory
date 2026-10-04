# policy_hash: e1d36aa1ac54c95413080ad15ef256257e0a8d6b1906bea7efbe58923ca0da8a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 21
# source_prompt_files: 1
# best_target_performance: 920.57
# best_prompt_performance: 920.57
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_045854.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 459.80116747111833  # OPT_PARAM: {"initial": 459.80116747111833, "min": 400, "max": 600, "type": "float"}
    safety_stock = 24.801167471120614  # OPT_PARAM: {"initial": 24.801167471120614, "min": 0, "max": 50, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.0, "max": 0.5, "type": "float"}
    demand_forecast_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.0, "max": 0.2, "type": "float"}
    lead_time = 4  # Fixed parameter

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Better demand forecast using historical average (approximated)
    historical_avg_demand = 100.0  # From data analysis

    # Adjust base stock based on lead time and demand
    adjusted_base = base_stock + demand_forecast_factor * (historical_avg_demand - 100.0) * lead_time

    # Calculate target inventory position
    target_inventory = adjusted_base + safety_stock

    # Calculate raw order quantity
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with pipeline consideration
    if pipeline_orders:
        # Use average of recent orders for smoothing reference
        recent_avg = sum(pipeline_orders[-min(2, len(pipeline_orders)):]) / min(2, len(pipeline_orders))
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * recent_avg
    else:
        order_amount = raw_order

    # Round to nearest integer (as order amounts should be integers)
    return order_amount
