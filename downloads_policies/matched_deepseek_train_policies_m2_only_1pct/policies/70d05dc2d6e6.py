# policy_hash: 70d05dc2d6e6c33587419fc04f42cac4ea3c35e5a95d591d2c51106e2351751a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 37
# source_prompt_files: 1
# best_target_performance: 3558.57
# best_prompt_performance: 3558.57
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_003014.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 451.9986772571328  # OPT_PARAM: {"initial": 451.9986772571328, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 95.04221109158341  # OPT_PARAM: {"initial": 95.04221109158341, "min": 0, "max": 300, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals
    # Use average of recent pipeline orders as demand proxy
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        forecast_demand = avg_pipeline * demand_forecast_factor
    else:
        forecast_demand = 0

    # Adjust base stock level dynamically
    adjusted_base_stock = base_stock + safety_stock - forecast_demand

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to avoid extreme order sizes
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    max_order_change = 90.35039224557163  # OPT_PARAM: {"initial": 90.35039224557163, "min": 10, "max": 200, "type": "float"}

    # If this is a large order, smooth it
    if order_amount > max_order_change:
        order_amount = max_order_change + (order_amount - max_order_change) * smoothing_factor

    return order_amount
