# policy_hash: 146c5682230c594a5d63608871ad3fe7f7928f6ac51dc15a980f1f105ac1d609
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 10247.08
# best_prompt_performance: 10246.9
# best_rel_error_pct: 0.001757
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_034139.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 282.84676129614553  # OPT_PARAM: {"initial": 282.84676129614553, "min": 200, "max": 350, "type": "float"}
    safety_stock = 43.277456743056234  # OPT_PARAM: {"initial": 43.277456743056234, "min": 30, "max": 70, "type": "float"}
    pipeline_coverage_factor = 0.853201130809229  # OPT_PARAM: {"initial": 0.853201130809229, "min": 0.7, "max": 1.0, "type": "float"}
    demand_anticipation_factor = 1.173500728532008  # OPT_PARAM: {"initial": 1.173500728532008, "min": 1.0, "max": 1.5, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand from recent pipeline orders
    if len(pipeline_orders) >= 2:
        recent_pipeline = pipeline_orders[-2:]
        estimated_demand = sum(recent_pipeline) / len(recent_pipeline)
    else:
        estimated_demand = base_stock / 4

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
