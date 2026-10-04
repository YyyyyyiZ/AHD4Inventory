# policy_hash: 23c64fb0517818a730c96557d3b26079be6a644b110a51103e76d97c625bdbda
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 45
# source_prompt_files: 1
# best_target_performance: 702.22
# best_prompt_performance: 702.22
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r9/prompt_for_code/m2_20260129_220043.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 310.0  # OPT_PARAM: {"initial": 310.0, "min": 250, "max": 400, "type": "float"}
    demand_forecast = 96.71828552558755  # OPT_PARAM: {"initial": 96.71828552558755, "min": 90, "max": 110, "type": "float"}
    safety_factor = 1.138730153276379  # OPT_PARAM: {"initial": 1.138730153276379, "min": 0.8, "max": 1.5, "type": "float"}
    pipeline_weight = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 0.8, "max": 1.2, "type": "float"}
    order_smoothing = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.5, "type": "float"}
    reorder_point = 204.96824292248397  # OPT_PARAM: {"initial": 204.96824292248397, "min": 150, "max": 250, "type": "float"}

    # Calculate inventory position with full pipeline weight
    weighted_pipeline = sum(p * pipeline_weight ** i for i, p in enumerate(reversed(pipeline_orders)))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time plus one period
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_forecast * (lead_time + 1)

    # Calculate safety stock based on demand variability
    safety_stock = safety_factor * demand_forecast * (lead_time ** 0.5)

    # Calculate target inventory level
    target_inventory = lead_time_demand + safety_stock

    # Only order if inventory position is below reorder point
    if inventory_position >= reorder_point:
        base_order = 0
    else:
        base_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = order_smoothing * base_order + (1 - order_smoothing) * demand_forecast

    # Apply base stock as upper bound
    order_amount = min(smoothed_order, base_stock)

    # Round to nearest integer for practical ordering
    return order_amount
