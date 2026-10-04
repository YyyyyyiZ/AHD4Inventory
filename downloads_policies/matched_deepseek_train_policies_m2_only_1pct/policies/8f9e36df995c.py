# policy_hash: 8f9e36df995c65f8abe765416bf248e718f40eb8532d4a7fdf18a41160fb336f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1280.51
# best_prompt_performance: 1275.46
# best_rel_error_pct: 0.394374
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_145925.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 451.91476510687255  # OPT_PARAM: {"initial": 451.91476510687255, "min": 350, "max": 550, "type": "float"}
    safety_stock = 42.54848232121164  # OPT_PARAM: {"initial": 42.54848232121164, "min": 30, "max": 100, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    demand_forecast_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.9, "max": 1.1, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.5, "type": "float"}
    variability_buffer = 2.944296837213433  # OPT_PARAM: {"initial": 2.944296837213433, "min": 0, "max": 30, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline average
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        demand_adjustment = demand_forecast_factor * avg_pipeline
    else:
        demand_adjustment = 0

    # Adjust target based on pipeline variability
    if len(pipeline_orders) > 1:
        pipeline_variability = max(pipeline_orders) - min(pipeline_orders)
    else:
        pipeline_variability = 0

    pipeline_effect = pipeline_weight * pipeline_variability

    # Dynamic target inventory with variability buffer
    target_inventory = base_stock + safety_stock - pipeline_effect + demand_adjustment + variability_buffer

    # Calculate order with smoothing
    raw_order = target_inventory - inventory_position
    order_amount = max(0, smoothing_factor * raw_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
