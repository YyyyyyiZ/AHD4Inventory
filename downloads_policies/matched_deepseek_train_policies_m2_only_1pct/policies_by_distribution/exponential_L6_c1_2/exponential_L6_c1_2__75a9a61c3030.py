# policy_hash: 75a9a61c303081b2c69698d842920791a281f87f27519c894e01bf44a3435f26
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 6048.86
# best_prompt_performance: 6048.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_094907.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 370.62536497519585  # OPT_PARAM: {"initial": 370.62536497519585, "min": 200, "max": 500, "type": "float"}
    pipeline_weight = 0.9121003730126073  # OPT_PARAM: {"initial": 0.9121003730126073, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.14564870331886756  # OPT_PARAM: {"initial": 0.14564870331886756, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock = 111.6443278026116  # OPT_PARAM: {"initial": 111.6443278026116, "min": 80, "max": 200, "type": "float"}
    demand_buffer = 1.2003693430932971  # OPT_PARAM: {"initial": 1.2003693430932971, "min": 1.0, "max": 1.3, "type": "float"}
    min_order_threshold = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 5, "max": 30, "type": "float"}
    pipeline_cap = 145.312655255957  # OPT_PARAM: {"initial": 145.312655255957, "min": 100, "max": 300, "type": "float"}
    max_order_size = 200.0  # OPT_PARAM: {"initial": 200.0, "min": 100, "max": 400, "type": "float"}

    # Calculate effective pipeline with cap to prevent over-reaction
    raw_pipeline = sum(pipeline_orders)
    capped_pipeline = min(raw_pipeline, pipeline_cap)
    effective_pipeline = capped_pipeline * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic safety stock based on recent pipeline variability
    if len(pipeline_orders) >= 3:
        recent_avg = (pipeline_orders[0] + pipeline_orders[1] + pipeline_orders[2]) / 3.0
        variability = abs(pipeline_orders[0] - recent_avg) / max(recent_avg, 1.0)
        dynamic_safety = safety_stock * (1.0 + min(variability, 0.5))
    else:
        dynamic_safety = safety_stock

    # Calculate target inventory
    target_inventory = base_stock + dynamic_safety

    # Calculate raw order amount with demand adjustment
    raw_order = max(0, target_inventory - inventory_position)

    # Apply demand-based scaling
    if raw_order > 0 and len(pipeline_orders) > 0:
        recent_demand = pipeline_orders[0]  # Most recent arrival as demand proxy
        if recent_demand > 0:
            adjusted_order = raw_order * demand_buffer
            raw_order = min(adjusted_order, raw_order * 1.5)

    # Apply smoothing and cap maximum order
    if raw_order > min_order_threshold:
        smoothed_order = raw_order * smoothing_factor
        order_amount = int(min(smoothed_order, max_order_size) + 0.5)
    else:
        order_amount = 0

    return order_amount
