# policy_hash: bc2e56f579ca641605b128e7b8a55c3c7f40d438024f71390242d909b6e77bba
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 1448.64
# best_prompt_performance: 1446.89
# best_rel_error_pct: 0.120803
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_095130.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 734.506118318454  # OPT_PARAM: {"initial": 734.506118318454, "min": 700, "max": 760, "type": "float"}
    safety_stock = 39.50611831845406  # OPT_PARAM: {"initial": 39.50611831845406, "min": 30, "max": 50, "type": "float"}
    pipeline_weight = 0.8436110687303985  # OPT_PARAM: {"initial": 0.8436110687303985, "min": 0.8, "max": 0.95, "type": "float"}
    demand_buffer = 24.506118318454053  # OPT_PARAM: {"initial": 24.506118318454053, "min": 20, "max": 30, "type": "float"}
    pipeline_threshold = 104.99979727453274  # OPT_PARAM: {"initial": 104.99979727453274, "min": 90, "max": 110, "type": "float"}
    adjustment_strength = 0.6872621452006991  # OPT_PARAM: {"initial": 0.6872621452006991, "min": 0.6, "max": 0.8, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 5, "type": "int"}
    max_order = 115  # OPT_PARAM: {"initial": 115, "min": 110, "max": 130, "type": "int"}
    smoothing_factor = 0.48721788618269984  # OPT_PARAM: {"initial": 0.48721788618269984, "min": 0.4, "max": 0.6, "type": "float"}
    pipeline_cap = 115.0  # OPT_PARAM: {"initial": 115.0, "min": 100, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline (weighted average favoring recent orders)
    if pipeline_orders:
        weights = [0.5**(len(pipeline_orders)-i) for i in range(len(pipeline_orders))]
        total_weight = sum(weights)
        weighted_pipeline = sum(w * q for w, q in zip(weights, pipeline_orders)) / total_weight
        effective_pipeline = min(weighted_pipeline, pipeline_cap)
    else:
        effective_pipeline = 0

    # Dynamic adjustment based on pipeline level
    if effective_pipeline > pipeline_threshold:
        adjustment = pipeline_weight * adjustment_strength
    else:
        adjustment = 1.0

    # Target inventory position with dynamic safety stock
    target_position = base_stock + safety_stock + demand_buffer
    smoothed_target = (target_position * smoothing_factor) + (inventory_position * (1 - smoothing_factor))

    # Calculate order amount with adjustment
    order_amount = max(0, (smoothed_target - inventory_position) * adjustment)

    # Apply order limits
    order_amount = max(min_order, min(max_order, order_amount))

    # Round to nearest integer
    return order_amount
