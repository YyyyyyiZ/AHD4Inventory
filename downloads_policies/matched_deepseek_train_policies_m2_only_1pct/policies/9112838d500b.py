# policy_hash: 9112838d500bece69b0cad3bff84ca5b5d2077d1b76d14e8a6b2d1f971fc1ee7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 2365.82
# best_prompt_performance: 2365.82
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_053621.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 462.02400088638166  # OPT_PARAM: {"initial": 462.02400088638166, "min": 100, "max": 800, "type": "float"}
    safety_stock = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 50, "max": 300, "type": "float"}
    demand_forecast = 72.18662668354627  # OPT_PARAM: {"initial": 72.18662668354627, "min": 70, "max": 150, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Dynamic safety stock based on pipeline variability
    if len(pipeline_orders) > 1:
        pipeline_std = (sum((p - demand_forecast) ** 2 for p in pipeline_orders) / len(pipeline_orders)) ** 0.5
        dynamic_safety = safety_stock + 0.5 * pipeline_std
    else:
        dynamic_safety = safety_stock

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + dynamic_safety

    # Use the minimum of base_stock and target_inventory for cost efficiency
    order_up_to = min(base_stock, target_inventory)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing only when order is significant
    if order_amount > demand_forecast:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
