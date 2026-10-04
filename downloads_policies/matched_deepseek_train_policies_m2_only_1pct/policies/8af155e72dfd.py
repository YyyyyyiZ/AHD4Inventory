# policy_hash: 8af155e72dfd2a9bd22a856ad5e5b27442d750ac13c2355f7d3fab6ccf6922ec
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 5618.78
# best_prompt_performance: 5616.7
# best_rel_error_pct: 0.037019
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_232658.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 533.8962259713829  # OPT_PARAM: {"initial": 533.8962259713829, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 49.94405582942226  # OPT_PARAM: {"initial": 49.94405582942226, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals
    # More weight on recent pipeline orders as they reflect recent demand patterns
    weighted_forecast = 0
    total_weight = 0
    for i, order in enumerate(pipeline_orders):
        weight = 1.0 / (i + 1)  # Decreasing weight for older orders
        weighted_forecast += order * weight
        total_weight += weight

    if total_weight > 0:
        avg_pipeline = weighted_forecast / total_weight
        forecast_demand = avg_pipeline * demand_forecast_factor
    else:
        forecast_demand = 0

    # Adjust base stock level based on demand forecast
    adjusted_base_stock = base_stock + safety_stock + forecast_demand

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply rounding to integer (common in practice)
    order_amount = int(round(order_amount))

    return order_amount
