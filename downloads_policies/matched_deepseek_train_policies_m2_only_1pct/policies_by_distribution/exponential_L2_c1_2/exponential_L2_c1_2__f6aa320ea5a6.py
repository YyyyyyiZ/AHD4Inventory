# policy_hash: f6aa320ea5a69dc9870b9bcce527f1cedc680ef078343de257bb3327512eaaed
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 32
# source_prompt_files: 2
# best_target_performance: 5887.72
# best_prompt_performance: 5887.74
# best_rel_error_pct: 0.000340
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_065257.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 210.0000005154503  # OPT_PARAM: {"initial": 210.0000005154503, "min": 150, "max": 350, "type": "float"}
    safety_stock = 40.000001472714196  # OPT_PARAM: {"initial": 40.000001472714196, "min": 20, "max": 100, "type": "float"}
    pipeline_coverage = 0.7544714649939412  # OPT_PARAM: {"initial": 0.7544714649939412, "min": 0.5, "max": 1.2, "type": "float"}
    demand_smoothing = 0.3757289956856193  # OPT_PARAM: {"initial": 0.3757289956856193, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_coverage
    inventory_position = on_hand_inventory + effective_pipeline

    # Simple base-stock policy with safety stock adjustment
    target_inventory = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply demand smoothing to avoid extreme fluctuations
    if raw_order > 0:
        smoothed_order = raw_order * demand_smoothing + (base_stock * 0.1) * (1 - demand_smoothing)
        order_amount = int(round(smoothed_order))
    else:
        order_amount = 0

    return order_amount
