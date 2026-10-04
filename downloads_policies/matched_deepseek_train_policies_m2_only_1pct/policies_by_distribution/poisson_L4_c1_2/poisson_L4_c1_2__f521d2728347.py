# policy_hash: f521d2728347af41b9583a25e559d6d1e1b7d0ecc94af70e2b541f25afdc1b8b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 823.2
# best_prompt_performance: 823.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_080217.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 284.3962896834373  # OPT_PARAM: {"initial": 284.3962896834373, "min": 250, "max": 350, "type": "float"}
    safety_stock = 32.91640533569117  # OPT_PARAM: {"initial": 32.91640533569117, "min": 20, "max": 60, "type": "float"}
    demand_forecast = 95.06559578492866  # OPT_PARAM: {"initial": 95.06559578492866, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.6205517233759327  # OPT_PARAM: {"initial": 0.6205517233759327, "min": 0.3, "max": 1.0, "type": "float"}
    lost_sales_weight = 1.0147371665385234  # OPT_PARAM: {"initial": 1.0147371665385234, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Weighted pipeline: emphasize imminent arrivals less
    weighted_pipeline = pipeline_orders[0] * pipeline_weight + sum(pipeline_orders[1:]) * (1 - pipeline_weight)
    effective_position = on_hand_inventory + weighted_pipeline

    # Dynamic target: increase safety stock when pipeline is low
    pipeline_ratio = sum(pipeline_orders) / (len(pipeline_orders) * demand_forecast)
    adjusted_safety = safety_stock * (1.0 + max(0, 1.0 - pipeline_ratio) * 0.3)

    # Target with lost-sales cost consideration
    target_inventory = base_stock + adjusted_safety * lost_sales_weight

    # Order calculation
    raw_order = max(0, target_inventory - effective_position)

    # Apply smoothing with demand forecast
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure order is integer and non-negative
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
