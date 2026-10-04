# policy_hash: 567cf9196a6586f76aa38050c703fd6a5cc95cd1b8daa7063715255f29b703bb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 45
# source_prompt_files: 1
# best_target_performance: 3868.54
# best_prompt_performance: 3868.44
# best_rel_error_pct: 0.002585
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_233947.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 380.00568674433816  # OPT_PARAM: {"initial": 380.00568674433816, "min": 200, "max": 600, "type": "float"}
    safety_stock = 80.1056867443383  # OPT_PARAM: {"initial": 80.1056867443383, "min": 30, "max": 200, "type": "float"}
    smoothing_factor = 0.15457956831940983  # OPT_PARAM: {"initial": 0.15457956831940983, "min": 0.1, "max": 0.8, "type": "float"}
    demand_forecast_factor = 0.5911477580680101  # OPT_PARAM: {"initial": 0.5911477580680101, "min": 0.5, "max": 2.0, "type": "float"}
    pipeline_weight = 0.9225242126057781  # OPT_PARAM: {"initial": 0.9225242126057781, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand from recent pipeline orders
    if len(pipeline_orders) > 0:
        # Use weighted average with more weight on recent orders
        weights = []
        for i, order in enumerate(pipeline_orders[-4:] if len(pipeline_orders) >= 4 else pipeline_orders):
            weight = pipeline_weight ** (len(pipeline_orders[-4:]) - i - 1)
            weights.append(weight)

        weighted_sum = sum(w * o for w, o in zip(weights, pipeline_orders[-4:] if len(pipeline_orders) >= 4 else pipeline_orders))
        expected_demand = weighted_sum / sum(weights) if sum(weights) > 0 else 0
    else:
        expected_demand = 0

    # Adjust base stock dynamically
    adjusted_base_stock = base_stock + safety_stock + (expected_demand * demand_forecast_factor)

    # Calculate raw order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing with adaptive factor based on inventory position
    smoothing = smoothing_factor * (1.0 - min(1.0, inventory_position / (adjusted_base_stock + 1e-6)))
    smoothed_order = raw_order * smoothing + (1 - smoothing) * expected_demand

    # Ensure order is at least expected demand when inventory is low
    if inventory_position < adjusted_base_stock * 0.3:
        smoothed_order = max(smoothed_order, expected_demand)

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
