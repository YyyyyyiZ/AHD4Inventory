# policy_hash: af3a7c99e69aab87fab6f4a401ac20daf4c697ebffc20a267fe5354b729ff4e5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 3803.49
# best_prompt_performance: 3803.74
# best_rel_error_pct: 0.006573
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_234401.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 442.65657199216434  # OPT_PARAM: {"initial": 442.65657199216434, "min": 300, "max": 600, "type": "float"}
    safety_stock = 72.65657199216226  # OPT_PARAM: {"initial": 72.65657199216226, "min": 50, "max": 150, "type": "float"}
    demand_forecast_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.2, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    recent_periods = 4  # OPT_PARAM: {"initial": 4, "min": 2, "max": 6, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand from recent pipeline orders
    if len(pipeline_orders) > 0:
        # Use configurable number of recent periods for demand forecasting
        recent_orders = pipeline_orders[-recent_periods:] if len(pipeline_orders) >= recent_periods else pipeline_orders
        expected_demand = sum(recent_orders) / len(recent_orders)
    else:
        expected_demand = 0

    # Adjust base stock based on expected demand
    adjusted_base_stock = base_stock + safety_stock + (expected_demand * demand_forecast_factor)

    # Calculate raw order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing with expected demand
    smoothed_order = raw_order * smoothing_factor + (1 - smoothing_factor) * expected_demand

    # Ensure order is non-negative integer
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
