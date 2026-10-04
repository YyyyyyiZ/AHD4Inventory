# policy_hash: da9cac29a5f413759b40d3397a9d41e2082a5f6b380f0dc5ef39bd0c7cd08e3f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1098.16
# best_prompt_performance: 1097.0
# best_rel_error_pct: 0.105631
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_000642.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 494.00000000000944  # OPT_PARAM: {"initial": 494.00000000000944, "min": 400, "max": 650, "type": "float"}
    safety_stock = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 10, "max": 50, "type": "float"}
    demand_forecast = 90.00000000000966  # OPT_PARAM: {"initial": 90.00000000000966, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    order_threshold = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with pipeline adjustment
    # Use weighted average of recent pipeline orders instead of just the last one
    recent_pipeline = sum(pipeline_orders[-2:]) / 2 if len(pipeline_orders) >= 2 else pipeline_orders[-1]
    pipeline_adjustment = pipeline_weight * recent_pipeline

    target_inventory = base_stock + safety_stock - pipeline_adjustment

    # Calculate order-up-to quantity
    order_needed = target_inventory - inventory_position

    # Apply smoothing with demand forecast
    if order_needed > demand_forecast * order_threshold:
        smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Ensure non-negative order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
