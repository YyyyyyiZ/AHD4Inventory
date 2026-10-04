# policy_hash: 073093f07067bd9cd29161531b887dadc7e7875dbe8c896a2fc6bc462148c792
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 45
# source_prompt_files: 1
# best_target_performance: 10237.94
# best_prompt_performance: 10237.8
# best_rel_error_pct: 0.001367
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_032815.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 230.76865008472723  # OPT_PARAM: {"initial": 230.76865008472723, "min": 200, "max": 450, "type": "float"}
    safety_stock = 113.68142176776969  # OPT_PARAM: {"initial": 113.68142176776969, "min": 40, "max": 120, "type": "float"}
    demand_forecast_weight = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast using recent pipeline arrivals
    if pipeline_orders:
        # Use weighted average with more weight to recent orders
        weights = [0.7, 0.3] if len(pipeline_orders) > 1 else [1.0]
        weighted_sum = sum(w * p for w, p in zip(weights, pipeline_orders[:len(weights)]))
        avg_weight = sum(weights[:len(pipeline_orders)])
        forecast_demand = weighted_sum / avg_weight if avg_weight > 0 else 0
    else:
        forecast_demand = 0

    # Adjust base stock with forecast
    adjusted_base_stock = base_stock + safety_stock + forecast_demand * demand_forecast_weight

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply order smoothing
    max_order_jump = 100.52033256631563  # OPT_PARAM: {"initial": 100.52033256631563, "min": 80, "max": 250, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.6, "type": "float"}

    if order_amount > max_order_jump:
        order_amount = max_order_jump + (order_amount - max_order_jump) * smoothing_factor

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
