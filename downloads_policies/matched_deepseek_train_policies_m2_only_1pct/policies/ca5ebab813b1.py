# policy_hash: ca5ebab813b1d4190324cb7fc573fea47c15ba915ead28014f077ec2d472b492
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 7011.51
# best_prompt_performance: 7011.1
# best_rel_error_pct: 0.005848
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_034813.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 272.5491227688055  # OPT_PARAM: {"initial": 272.5491227688055, "min": 200, "max": 600, "type": "float"}
    safety_stock = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 100, "type": "float"}
    pipeline_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.3, "type": "float"}
    demand_forecast_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline arrivals
    # Use average of oldest 3 pipeline orders as demand proxy
    if len(pipeline_orders) >= 3:
        recent_arrivals = pipeline_orders[:3]
        forecast_demand = sum(recent_arrivals) / len(recent_arrivals) * demand_forecast_factor
    else:
        forecast_demand = 0

    # Adjust base stock based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    if pipeline_sum > 0:
        pipeline_avg = pipeline_sum / len(pipeline_orders)
        pipeline_variability = sum(abs(p - pipeline_avg) for p in pipeline_orders) / pipeline_sum
        # Less aggressive adjustment than before
        adjusted_base = base_stock * (1 + pipeline_variability * pipeline_factor)
    else:
        adjusted_base = base_stock

    # Incorporate demand forecast into target
    target_inventory = adjusted_base + safety_stock + forecast_demand

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer
    return order_amount
