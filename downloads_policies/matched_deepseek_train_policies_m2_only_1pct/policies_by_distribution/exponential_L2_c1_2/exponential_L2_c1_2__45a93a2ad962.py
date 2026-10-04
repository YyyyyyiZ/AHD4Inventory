# policy_hash: 45a93a2ad9621b01857d3a3d5ad4516945ca021009599fdea9e306dae1987601
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 5885.76
# best_prompt_performance: 5885.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_225442.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 176.7356237931073  # OPT_PARAM: {"initial": 176.7356237931073, "min": 100, "max": 300, "type": "float"}
    safety_factor = 2.482320217143441  # OPT_PARAM: {"initial": 2.482320217143441, "min": 1.5, "max": 4.0, "type": "float"}
    pipeline_coverage = 0.7892747545892665  # OPT_PARAM: {"initial": 0.7892747545892665, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing = 0.38089695429688686  # OPT_PARAM: {"initial": 0.38089695429688686, "min": 0.2, "max": 0.8, "type": "float"}
    min_order = 10  # OPT_PARAM: {"initial": 10, "min": 0, "max": 50, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand variability from pipeline (recent orders reflect demand)
    if len(pipeline_orders) >= 2:
        recent_orders = pipeline_orders[-2:]  # Focus on most recent orders
        avg_recent = sum(recent_orders) / len(recent_orders)
        var = sum((x - avg_recent) ** 2 for x in recent_orders) / len(recent_orders)
        std_est = var ** 0.5 if var > 0 else avg_recent * 0.3
    else:
        std_est = base_stock * 0.25

    # Safety stock
    safety_stock = safety_factor * std_est

    # Adjust for pipeline: reduce target if pipeline already covers expected demand
    total_pipeline = sum(pipeline_orders)
    expected_coverage = base_stock * len(pipeline_orders) * pipeline_coverage
    pipeline_shortfall = max(0, expected_coverage - total_pipeline)

    # Target inventory position
    target = base_stock + safety_stock + pipeline_shortfall * 0.3

    # Order needed
    order_needed = target - inventory_position

    # Smooth large orders
    if abs(order_needed) > base_stock * 0.5:
        order_needed = order_needed * smoothing

    # Ensure minimum order size when ordering
    if order_needed > min_order:
        order_amount = int(round(order_needed))
    elif order_needed > 0:
        order_amount = min_order
    else:
        order_amount = 0

    return order_amount
