# policy_hash: 812631d545b109ae42d51f81a64a1c9709f90c5989547b52458e15b9c6fbbde0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 6162.72
# best_prompt_performance: 6162.72
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_080752.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 278.5112053168856  # OPT_PARAM: {"initial": 278.5112053168856, "min": 200, "max": 400, "type": "float"}
    safety_stock = 45.2  # OPT_PARAM: {"initial": 45.2, "min": 20, "max": 80, "type": "float"}
    demand_forecast_factor = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 0.7, "max": 1.1, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    lost_sales_weight = 1.705353885570085  # OPT_PARAM: {"initial": 1.705353885570085, "min": 1.2, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted average of recent pipeline orders
    if len(pipeline_orders) > 0:
        # Use only recent orders for better responsiveness
        recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
        weights = [pipeline_weight ** i for i in range(len(recent_orders))]
        weighted_sum = sum(w * q for w, q in zip(weights, recent_orders))
        total_weight = sum(weights)
        demand_estimate = (weighted_sum / total_weight) * demand_forecast_factor
    else:
        demand_estimate = 0

    # Adjust base stock based on cost ratio (p/h = 2)
    # Higher weight on lost sales to reduce stockouts
    cost_adjusted_base = base_stock * (lost_sales_weight / 2.0)

    # Dynamic base stock with demand estimate
    adjusted_base_stock = cost_adjusted_base + demand_estimate

    # Ensure minimum safety stock
    order_up_to = max(adjusted_base_stock, safety_stock)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply moderate smoothing
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
