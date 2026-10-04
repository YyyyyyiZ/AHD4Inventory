# policy_hash: 8d615aad52a3e96e280d95e6f1512c4b62f1a103b6220d39d4af8f0b2d1b51e5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 1401.8
# best_prompt_performance: 1401.8
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_025616.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 231.8117292558571  # OPT_PARAM: {"initial": 231.8117292558571, "min": 100, "max": 400, "type": "float"}
    safety_stock = 16.91172925585701  # OPT_PARAM: {"initial": 16.91172925585701, "min": 0, "max": 50, "type": "float"}
    demand_forecast_factor = 0.7488986247974071  # OPT_PARAM: {"initial": 0.7488986247974071, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent pipeline orders
    # More weight to recent orders as they better reflect current demand pattern
    if len(pipeline_orders) >= 2:
        # Weight recent orders more heavily
        recent_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.5, "max": 0.9, "type": "float"}
        older_weight = 1 - recent_weight

        if len(pipeline_orders) == 2:
            expected_demand = (recent_weight * pipeline_orders[-1] +
                             older_weight * pipeline_orders[-2]) * demand_forecast_factor
        else:
            # For L>2, use average of last two orders
            expected_demand = ((pipeline_orders[-1] + pipeline_orders[-2]) / 2) * demand_forecast_factor
    elif pipeline_orders:
        expected_demand = pipeline_orders[-1] * demand_forecast_factor
    else:
        expected_demand = 100.0 * demand_forecast_factor  # Default estimate

    # Dynamic base stock adjustment based on expected demand
    # Higher expected demand → higher base stock
    demand_adjustment = 0.7205025613981536  # OPT_PARAM: {"initial": 0.7205025613981536, "min": 0.5, "max": 1.5, "type": "float"}
    adjusted_base_stock = base_stock + safety_stock + (expected_demand * demand_adjustment)

    # Calculate order amount using base-stock policy
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply moderate smoothing to reduce order volatility
    smoothing_factor = 0.3070012238246569  # OPT_PARAM: {"initial": 0.3070012238246569, "min": 0.2, "max": 0.8, "type": "float"}
    if pipeline_orders:
        previous_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * previous_order
        order_amount = max(0, smoothed_order)

    # Ensure order amount is non-negative integer
    order_amount = int(round(order_amount))

    return order_amount
