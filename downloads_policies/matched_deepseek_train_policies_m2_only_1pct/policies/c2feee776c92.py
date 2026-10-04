# policy_hash: c2feee776c921edf6f4f61c27fe18a4fdf9a58b1f12fe01daa148c5581be435a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 3770.5
# best_prompt_performance: 3767.84
# best_rel_error_pct: 0.070548
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_001402.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 430.6720195984  # OPT_PARAM: {"initial": 430.6720195984, "min": 400, "max": 550, "type": "float"}
    safety_stock = 63.40883880757675  # OPT_PARAM: {"initial": 63.40883880757675, "min": 60, "max": 120, "type": "float"}
    demand_forecast_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.9, "max": 1.2, "type": "float"}
    smoothing_factor = 0.15000000000000002  # OPT_PARAM: {"initial": 0.15000000000000002, "min": 0.05, "max": 0.3, "type": "float"}
    recent_periods = 8  # OPT_PARAM: {"initial": 8, "min": 4, "max": 12, "type": "int"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.3, "max": 0.8, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand from recent pipeline orders
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-recent_periods:] if len(pipeline_orders) >= recent_periods else pipeline_orders
        expected_demand = sum(recent_orders) / len(recent_orders)
    else:
        expected_demand = 0

    # Adjust base stock with safety stock and demand forecast
    adjusted_base_stock = base_stock + safety_stock + (expected_demand * demand_forecast_factor)

    # Apply lost-sales penalty adjustment (since p > h)
    target_inventory = adjusted_base_stock * lost_sales_weight

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing
    smoothed_order = raw_order * smoothing_factor + (1 - smoothing_factor) * expected_demand

    # Ensure order is non-negative integer
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
