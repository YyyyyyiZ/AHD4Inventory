# policy_hash: 5355b7e582ed7e18601ae6d17b06caf25c2ce3e946917d3d855cb68a9873211a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 5365.01
# best_prompt_performance: 5367.87
# best_rel_error_pct: 0.053308
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_233125.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 474.2700118405396  # OPT_PARAM: {"initial": 474.2700118405396, "min": 300, "max": 700, "type": "float"}
    safety_stock = 5.011487600297191  # OPT_PARAM: {"initial": 5.011487600297191, "min": 0, "max": 100, "type": "float"}
    demand_smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    pipeline_weight = 0.21331483297069823  # OPT_PARAM: {"initial": 0.21331483297069823, "min": 0.1, "max": 1.0, "type": "float"}
    recent_window = 4  # OPT_PARAM: {"initial": 4, "min": 1, "max": 6, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline contribution
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders[:recent_window]):
        weight = pipeline_weight ** (i + 1)
        weighted_pipeline += order * weight

    # Calculate expected demand adjustment
    if len(pipeline_orders) >= recent_window:
        recent_arrivals = pipeline_orders[:recent_window]
        avg_recent = sum(recent_arrivals) / len(recent_arrivals)
        demand_adjustment = demand_smoothing_factor * avg_recent
    else:
        demand_adjustment = 0

    # Calculate target inventory with adjustments
    target_inventory = base_stock + safety_stock + demand_adjustment + weighted_pipeline

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply integer rounding
    return order_amount
