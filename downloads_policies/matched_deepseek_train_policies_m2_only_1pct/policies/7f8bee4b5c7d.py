# policy_hash: 7f8bee4b5c7dceaddd9e611015a7293941e85d66269e1e523e176d5bd6aae288
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 11017.77
# best_prompt_performance: 11017.77
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_050226.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 377.6197514666072  # OPT_PARAM: {"initial": 377.6197514666072, "min": 200, "max": 500, "type": "float"}
    safety_stock = 81.90829515131703  # OPT_PARAM: {"initial": 81.90829515131703, "min": 40, "max": 120, "type": "float"}
    demand_forecast_factor = 1.476665438571927  # OPT_PARAM: {"initial": 1.476665438571927, "min": 0.8, "max": 1.5, "type": "float"}
    order_smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}
    lost_sales_weight = 2.4073950628485723  # OPT_PARAM: {"initial": 2.4073950628485723, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast using recent pipeline arrivals
    if len(pipeline_orders) > 0:
        # Use exponential weighting for recent orders
        weights = [0.6, 0.25, 0.1, 0.05][:len(pipeline_orders)]
        weights = [w/sum(weights) for w in weights]
        forecast = sum(w * d for w, d in zip(weights, pipeline_orders))
        forecast = forecast * demand_forecast_factor
    else:
        forecast = 0

    # Adjust base stock based on pipeline status
    pipeline_sum = sum(pipeline_orders)
    pipeline_adjustment = pipeline_sum * pipeline_weight

    # Adjust safety stock based on cost ratio (higher penalty for lost sales)
    adjusted_safety = safety_stock * lost_sales_weight

    # Target inventory level
    target_inventory = base_stock + adjusted_safety + forecast - pipeline_adjustment

    # Calculate order needed
    order_needed = max(0, target_inventory - inventory_position)

    # Apply order smoothing
    if order_needed > 0:
        order_amount = order_needed * order_smoothing
    else:
        order_amount = 0

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
