# policy_hash: b0abed89e9f5fd451858d2e7f978cb45673285b28c517095d4d620a5b42dfca3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 10164.58
# best_prompt_performance: 10164.58
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_232224.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 386.3509251492156  # OPT_PARAM: {"initial": 386.3509251492156, "min": 100, "max": 800, "type": "float"}
    safety_stock = 3.19757963816528e-14  # OPT_PARAM: {"initial": 3.19757963816528e-14, "min": 0, "max": 100, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    pipeline_weight_factor = 0.15  # OPT_PARAM: {"initial": 0.15, "min": 0.0, "max": 0.5, "type": "float"}
    smoothing_factor = 0.35225218316223517  # OPT_PARAM: {"initial": 0.35225218316223517, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple weighted pipeline calculation
    weighted_pipeline = 0
    for i, q in enumerate(pipeline_orders):
        weight = 1.0 / (i + 1)
        weighted_pipeline += q * weight

    # Adjust target based on pipeline distribution
    total_pipeline = sum(pipeline_orders)
    if total_pipeline > 0:
        avg_weight = weighted_pipeline / total_pipeline
        pipeline_adjustment = 1.0 + (avg_weight - 1.0) * pipeline_weight_factor
    else:
        pipeline_adjustment = 1.0

    # Calculate target inventory position
    target = base_stock * pipeline_adjustment + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target - inventory_position)

    # Apply smoothing with demand forecast
    if raw_order > 0:
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast_factor * base_stock
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
