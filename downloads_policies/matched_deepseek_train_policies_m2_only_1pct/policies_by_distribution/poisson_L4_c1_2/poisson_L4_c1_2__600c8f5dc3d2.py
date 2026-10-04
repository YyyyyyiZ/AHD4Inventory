# policy_hash: 600c8f5dc3d2c8ac8d017e2a53f934e349fe30d1ab29ddee05e273613cac7a19
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 833.0
# best_prompt_performance: 833.0
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_080528.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 423.3217866395911  # OPT_PARAM: {"initial": 423.3217866395911, "min": 380, "max": 480, "type": "float"}
    safety_stock = 27.055819746428234  # OPT_PARAM: {"initial": 27.055819746428234, "min": 15, "max": 40, "type": "float"}
    demand_forecast = 95.3995106140461  # OPT_PARAM: {"initial": 95.3995106140461, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple base-stock policy with safety stock
    target_inventory = base_stock + safety_stock

    # Calculate raw order quantity
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure minimum order when inventory is below target
    if inventory_position < target_inventory:
        smoothed_order = max(smoothed_order, demand_forecast * 0.7)

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
