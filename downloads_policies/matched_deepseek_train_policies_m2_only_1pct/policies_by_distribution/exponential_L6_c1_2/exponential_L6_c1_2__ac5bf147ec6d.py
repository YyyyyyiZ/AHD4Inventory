# policy_hash: ac5bf147ec6d5652b8272c211ba557c77a9ace2efe9c170f677fe889f66bb44d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 7022.95
# best_prompt_performance: 7017.55
# best_rel_error_pct: 0.076891
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_035717.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 321.5532071626037  # OPT_PARAM: {"initial": 321.5532071626037, "min": 250, "max": 500, "type": "float"}
    safety_stock = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 80, "type": "float"}
    pipeline_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    demand_forecast_factor = 0.637849809730576  # OPT_PARAM: {"initial": 0.637849809730576, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_lookback = 2  # OPT_PARAM: {"initial": 2, "min": 1, "max": 4, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline arrivals
    # Use average of oldest pipeline_lookback orders as demand proxy
    if len(pipeline_orders) >= pipeline_lookback:
        recent_arrivals = pipeline_orders[:pipeline_lookback]
        forecast_demand = sum(recent_arrivals) / len(recent_arrivals) * demand_forecast_factor
    else:
        forecast_demand = 0

    # Adjust base stock based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    if pipeline_sum > 0:
        pipeline_avg = pipeline_sum / len(pipeline_orders)
        pipeline_variability = sum(abs(p - pipeline_avg) for p in pipeline_orders) / pipeline_sum
        # Moderate adjustment for pipeline variability
        adjusted_base = base_stock * (1 + pipeline_variability * pipeline_factor)
    else:
        adjusted_base = base_stock

    # Incorporate demand forecast and safety stock into target
    target_inventory = adjusted_base + safety_stock + forecast_demand

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer
    return order_amount
