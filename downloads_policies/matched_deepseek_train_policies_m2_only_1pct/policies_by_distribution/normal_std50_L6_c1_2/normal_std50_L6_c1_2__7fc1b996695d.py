# policy_hash: 7fc1b996695d0f032f5e87c48bc9443c6c130fd3c633a62fd168bff7099d0da7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 36
# source_prompt_files: 1
# best_target_performance: 3811.68
# best_prompt_performance: 3811.42
# best_rel_error_pct: 0.006821
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_001246.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 444.081836662876  # OPT_PARAM: {"initial": 444.081836662876, "min": 300, "max": 700, "type": "float"}
    safety_stock = 74.08183666287432  # OPT_PARAM: {"initial": 74.08183666287432, "min": 40, "max": 150, "type": "float"}
    demand_forecast_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.2, "type": "float"}
    smoothing_factor = 0.11932452870251668  # OPT_PARAM: {"initial": 0.11932452870251668, "min": 0.05, "max": 0.5, "type": "float"}
    recent_periods = 4  # OPT_PARAM: {"initial": 4, "min": 2, "max": 8, "type": "int"}

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
