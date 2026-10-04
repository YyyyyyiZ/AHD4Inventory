# policy_hash: e288c336d2ace427f951ca6890cb371660a2d76282f2f865adc0f9a58d2ca401
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 21
# source_prompt_files: 1
# best_target_performance: 10227.67
# best_prompt_performance: 10227.67
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_033805.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 319.0174087582587  # OPT_PARAM: {"initial": 319.0174087582587, "min": 200, "max": 450, "type": "float"}
    safety_stock = 39.05245933052077  # OPT_PARAM: {"initial": 39.05245933052077, "min": 20, "max": 80, "type": "float"}
    pipeline_coverage_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.6, "max": 1.0, "type": "float"}
    demand_anticipation_factor = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 1.0, "max": 1.4, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand from recent pipeline orders
    # Recent pipeline orders reflect recent demand patterns
    if len(pipeline_orders) >= 2:
        recent_pipeline = pipeline_orders[-2:]
        estimated_demand = sum(recent_pipeline) / len(recent_pipeline)
    else:
        estimated_demand = base_stock / 4  # Fallback estimate

    # Adjust base stock based on estimated demand
    adjusted_base_stock = base_stock * demand_anticipation_factor * (estimated_demand / (base_stock / 4))

    # Account for pipeline coverage
    pipeline_cover = sum(pipeline_orders) * pipeline_coverage_factor

    # Calculate target inventory level
    target_inventory = adjusted_base_stock + safety_stock - pipeline_cover

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Smooth with previous order pattern
    if pipeline_orders:
        recent_order_avg = sum(pipeline_orders[-2:]) / 2 if len(pipeline_orders) >= 2 else pipeline_orders[-1]
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * recent_order_avg
    else:
        order_amount = raw_order

    # Ensure non-negative integer
    return order_amount
