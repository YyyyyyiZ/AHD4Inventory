# policy_hash: 2192dd99dd8525c68374d689ad5cff6afc9fae54f9057e08194a5e35c6c8bd58
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 5378.27
# best_prompt_performance: 5376.42
# best_rel_error_pct: 0.034398
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_234021.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 418.1138451962267  # OPT_PARAM: {"initial": 418.1138451962267, "min": 300, "max": 700, "type": "float"}
    safety_stock = 13.113845196226091  # OPT_PARAM: {"initial": 13.113845196226091, "min": 0, "max": 100, "type": "float"}
    demand_smoothing_factor = 0.09243687597657947  # OPT_PARAM: {"initial": 0.09243687597657947, "min": 0.01, "max": 0.2, "type": "float"}
    pipeline_weight = 0.5326100708695354  # OPT_PARAM: {"initial": 0.5326100708695354, "min": 0.1, "max": 1.0, "type": "float"}
    recent_window = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 6, "type": "int"}
    adjustment_factor = 0.7327485152479375  # OPT_PARAM: {"initial": 0.7327485152479375, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline contribution (exponential decay)
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders[:recent_window]):
        weight = pipeline_weight ** (i + 1)
        weighted_pipeline += order * weight

    # Calculate expected demand adjustment using recent arrivals
    if len(pipeline_orders) >= recent_window:
        recent_arrivals = pipeline_orders[:recent_window]
        avg_recent = sum(recent_arrivals) / len(recent_arrivals)
        demand_adjustment = demand_smoothing_factor * avg_recent
    else:
        demand_adjustment = 0

    # Calculate target inventory with adjustments
    target_inventory = base_stock + safety_stock + demand_adjustment + adjustment_factor * weighted_pipeline

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply integer rounding
    return order_amount
