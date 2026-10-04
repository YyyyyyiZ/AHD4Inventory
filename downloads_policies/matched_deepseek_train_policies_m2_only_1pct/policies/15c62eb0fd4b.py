# policy_hash: 15c62eb0fd4b66b7b6f63050efac4d42cc837e8f011173da379997cb4595ba3b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 5437.39
# best_prompt_performance: 5440.82
# best_rel_error_pct: 0.063082
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_003436.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 471.2801904813115  # OPT_PARAM: {"initial": 471.2801904813115, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 1.5516631158576868  # OPT_PARAM: {"initial": 1.5516631158576868, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.1, "max": 1.0, "type": "float"}
    demand_forecast_factor = 0.5674705163211606  # OPT_PARAM: {"initial": 0.5674705163211606, "min": 0.5, "max": 2.0, "type": "float"}
    inventory_coverage = 1.0087013131910323  # OPT_PARAM: {"initial": 1.0087013131910323, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate effective pipeline with weighted aging
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_weight ** i
        weighted_pipeline += order * weight

    # Calculate average historical demand from the last few periods
    # Use a simple moving average approach based on pipeline orders
    # This gives a rough estimate of recent demand patterns
    recent_orders_sum = sum(pipeline_orders[:3]) if len(pipeline_orders) >= 3 else sum(pipeline_orders)
    recent_periods = min(3, len(pipeline_orders))
    avg_recent_demand = recent_orders_sum / recent_periods if recent_periods > 0 else 0

    # Adjust base stock based on safety stock and demand forecast
    forecast_adjustment = avg_recent_demand * demand_forecast_factor
    adjusted_base = (base_stock + safety_stock) * inventory_coverage + forecast_adjustment

    # Calculate net inventory position
    net_inventory = on_hand_inventory + weighted_pipeline

    # Calculate order amount with smoothing
    order_amount = max(0, adjusted_base - net_inventory)

    # Add a small buffer for high variability periods
    if avg_recent_demand > base_stock * 0.3:
        order_amount = order_amount * 1.1

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
