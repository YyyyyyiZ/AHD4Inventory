# policy_hash: ac00e3a17df3ca620abc79efa7a73c8b03fbeb331d4c83a8747996db18196d26
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 2378.1
# best_prompt_performance: 2378.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_022741.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 695.4311327849402  # OPT_PARAM: {"initial": 695.4311327849402, "min": 400, "max": 900, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 20, "max": 200, "type": "float"}
    demand_forecast_factor = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 0.5, "max": 2.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.8, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    demand_shift = -30.471268636400396  # OPT_PARAM: {"initial": -30.471268636400396, "min": -50, "max": 50, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline for demand forecasting
    if len(pipeline_orders) > 0:
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders))]
        weighted_pipeline = sum(w * q for w, q in zip(weights, pipeline_orders))
        total_weight = sum(weights)
        avg_weighted_demand = weighted_pipeline / total_weight
    else:
        avg_weighted_demand = 100.0

    # Adjust base stock based on demand forecast with shift
    demand_adjustment = demand_forecast_factor * (avg_weighted_demand - 100 + demand_shift)
    adjusted_base_stock = base_stock + demand_adjustment

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base_stock, safety_stock)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing using recent pipeline orders
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-min(3, len(pipeline_orders)):]
        avg_recent = sum(recent_orders) / len(recent_orders)
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_recent
        order_amount = max(0, smoothed_order)

    # Adjust for lost sales cost ratio (p/h = 2)
    # Increase orders when inventory is low relative to recent demand
    if len(pipeline_orders) > 0:
        recent_demand_estimate = sum(pipeline_orders[-min(2, len(pipeline_orders)):]) / min(2, len(pipeline_orders))
        if on_hand_inventory < recent_demand_estimate:
            order_amount *= lost_sales_weight

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
