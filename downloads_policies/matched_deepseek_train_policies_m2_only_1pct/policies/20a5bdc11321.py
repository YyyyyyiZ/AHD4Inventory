# policy_hash: 20a5bdc11321ca5f06c3a24414b97710e777bbb8edec17952dac8ca00a05def8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1535.08
# best_prompt_performance: 1535.84
# best_rel_error_pct: 0.049509
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_093610.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 748.1367997510473  # OPT_PARAM: {"initial": 748.1367997510473, "min": 700, "max": 760, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 30, "max": 50, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 0.95, "type": "float"}
    demand_buffer = 30.0  # OPT_PARAM: {"initial": 30.0, "min": 20, "max": 30, "type": "float"}
    pipeline_threshold = 102.72270856098095  # OPT_PARAM: {"initial": 102.72270856098095, "min": 90, "max": 110, "type": "float"}
    adjustment_strength = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 0.8, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 5, "type": "int"}
    max_order = 120  # OPT_PARAM: {"initial": 120, "min": 110, "max": 130, "type": "int"}
    smoothing_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.6, "type": "float"}
    pipeline_cap = 110.0  # OPT_PARAM: {"initial": 110.0, "min": 100, "max": 120, "type": "float"}

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
