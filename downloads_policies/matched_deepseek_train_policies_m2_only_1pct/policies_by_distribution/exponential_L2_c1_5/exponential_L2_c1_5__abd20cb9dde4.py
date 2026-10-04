# policy_hash: abd20cb9dde467b051ada92d2697b4e44b2c291a08e159da10b23e3b5d146579
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 10161.87
# best_prompt_performance: 10161.87
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_232603.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 446.1391748856852  # OPT_PARAM: {"initial": 446.1391748856852, "min": 100, "max": 800, "type": "float"}
    safety_stock = 16.239174885684356  # OPT_PARAM: {"initial": 16.239174885684356, "min": 0, "max": 100, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.0, "max": 1.0, "type": "float"}
    smoothing = 0.34865224260016286  # OPT_PARAM: {"initial": 0.34865224260016286, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline (weighted average with more weight on near arrivals)
    effective_pipeline = 0
    total_weight = 0
    for i, q in enumerate(pipeline_orders):
        weight = pipeline_weight ** (len(pipeline_orders) - i - 1)  # More weight to recent orders
        effective_pipeline += q * weight
        total_weight += weight

    if total_weight > 0:
        effective_pipeline = effective_pipeline / total_weight

    # Adjust target based on pipeline concentration
    pipeline_adjustment = 1.0
    if len(pipeline_orders) > 0 and sum(pipeline_orders) > 0:
        # If pipeline is concentrated in near future, reduce target
        concentration = effective_pipeline / (sum(pipeline_orders) / len(pipeline_orders))
        pipeline_adjustment = 1.0 / (1.0 + 0.2 * (concentration - 1.0))

    # Target inventory position
    target = base_stock * pipeline_adjustment + safety_stock

    # Order needed to reach target
    order_needed = max(0, target - inventory_position)

    # Apply smoothing
    order_amount = smoothing * order_needed

    # Round to nearest integer
    return order_amount
