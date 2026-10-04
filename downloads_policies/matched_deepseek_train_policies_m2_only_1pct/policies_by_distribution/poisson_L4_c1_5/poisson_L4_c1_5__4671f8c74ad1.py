# policy_hash: 4671f8c74ad10d2e62126b3f6e4454174fd3d88f4c680fce507856ffaeb2096a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 2310.28
# best_prompt_performance: 2312.6
# best_rel_error_pct: 0.100421
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_042048.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 502.25325231431265  # OPT_PARAM: {"initial": 502.25325231431265, "min": 300, "max": 600, "type": "float"}
    safety_stock = 75.0  # OPT_PARAM: {"initial": 75.0, "min": 30, "max": 150, "type": "float"}
    demand_forecast = 98.5  # OPT_PARAM: {"initial": 98.5, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.3, "max": 0.9, "type": "float"}
    lost_sales_weight = 3.5  # OPT_PARAM: {"initial": 3.5, "min": 1.0, "max": 5.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety adjustment
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Adjust safety stock based on cost ratio (p/h = 5)
    adjusted_safety = safety_stock * lost_sales_weight

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + adjusted_safety

    # Use the minimum of base_stock and target_inventory for tighter control
    order_up_to = min(base_stock, target_inventory)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply stronger smoothing to reduce order volatility
    if len(pipeline_orders) > 0:
        previous_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * previous_order
        order_amount = max(0, int(round(smoothed_order)))
    else:
        order_amount = max(0, int(round(order_amount)))

    return order_amount
