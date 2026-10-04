# policy_hash: 86ade472c7240371f928680bd673b6f9cdda6b4b612e8f257681609e327bea66
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 40
# source_prompt_files: 1
# best_target_performance: 10223.89
# best_prompt_performance: 10223.89
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_034231.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 374.7832085781123  # OPT_PARAM: {"initial": 374.7832085781123, "min": 300, "max": 500, "type": "float"}
    safety_stock = 21.43532851276952  # OPT_PARAM: {"initial": 21.43532851276952, "min": 10, "max": 50, "type": "float"}
    pipeline_coverage_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.6, "max": 1.0, "type": "float"}
    demand_anticipation_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}
    demand_estimation_window = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 5, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand from recent pipeline orders
    # Use configurable window size for better adaptability
    if len(pipeline_orders) >= demand_estimation_window:
        recent_pipeline = pipeline_orders[-demand_estimation_window:]
        estimated_demand = sum(recent_pipeline) / len(recent_pipeline)
    else:
        estimated_demand = base_stock / 4  # Fallback estimate

    # Adjust base stock based on estimated demand with bounded factor
    demand_ratio = estimated_demand / (base_stock / 4)
    demand_ratio = max(0.5, min(2.0, demand_ratio))  # Bound the ratio to avoid extreme adjustments
    adjusted_base_stock = base_stock * demand_anticipation_factor * demand_ratio

    # Account for pipeline coverage
    pipeline_cover = sum(pipeline_orders) * pipeline_coverage_factor

    # Calculate target inventory level
    target_inventory = adjusted_base_stock + safety_stock - pipeline_cover

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Smooth with previous order pattern using configurable factor
    if pipeline_orders:
        recent_order_avg = sum(pipeline_orders[-2:]) / 2 if len(pipeline_orders) >= 2 else pipeline_orders[-1]
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * recent_order_avg
    else:
        order_amount = raw_order

    # Ensure non-negative integer
    return order_amount
