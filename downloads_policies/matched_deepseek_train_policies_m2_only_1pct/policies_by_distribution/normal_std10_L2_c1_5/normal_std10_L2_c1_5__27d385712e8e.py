# policy_hash: 27d385712e8ea00b332705c3e692c9b4f8784450bc998f06f591a86848fba87c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1337.44
# best_prompt_performance: 1337.92
# best_rel_error_pct: 0.035889
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_090446.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 308.1003179933655  # OPT_PARAM: {"initial": 308.1003179933655, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 0, "max": 100, "type": "float"}
    demand_adjustment_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    if len(pipeline_orders) >= 2 and pipeline_orders[0] > 0:
        recent_arrivals = [p for p in pipeline_orders[:2] if p > 0]
        if recent_arrivals:
            avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
        else:
            avg_recent_demand = 100.0  # default estimate
    else:
        avg_recent_demand = 100.0  # default estimate

    # Adjust base stock based on recent demand pattern
    adjusted_base_stock = base_stock + (avg_recent_demand - 100) * demand_adjustment_factor

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base_stock, safety_stock + avg_recent_demand * 2)

    # Calculate order amount
    order_amount = max(0, order_up_to - net_inventory)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.1, "max": 1.0, "type": "float"}
    if pipeline_orders and len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        if order_amount > avg_pipeline * 2:
            order_amount = avg_pipeline * 2 * smoothing_factor + order_amount * (1 - smoothing_factor)

    return order_amount
