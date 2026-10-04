# policy_hash: 75413c38ddd011cb5e103886bc560ae175d02075c2c6552295662bc6f86536e8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 814.24
# best_prompt_performance: 814.92
# best_rel_error_pct: 0.083513
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_001548.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 478.93419474060295  # OPT_PARAM: {"initial": 478.93419474060295, "min": 400, "max": 600, "type": "float"}
    safety_stock = 35.0  # OPT_PARAM: {"initial": 35.0, "min": 20, "max": 60, "type": "float"}
    demand_forecast = 93.56604791413824  # OPT_PARAM: {"initial": 93.56604791413824, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level with adjusted safety stock
    target_inventory = expected_lead_time_demand + safety_stock

    # Use maximum of base_stock and target_inventory as order-up-to level
    order_up_to = max(base_stock, target_inventory)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with pipeline-aware adjustment
    # Give more weight to pipeline when it's low
    pipeline_coverage = sum(pipeline_orders) / (demand_forecast * len(pipeline_orders) + 1e-6)
    adjusted_smoothing = smoothing_factor * (1.0 + 0.5 * max(0, 1 - pipeline_coverage))
    adjusted_smoothing = min(0.5, adjusted_smoothing)  # Cap smoothing

    smoothed_order = adjusted_smoothing * raw_order + (1 - adjusted_smoothing) * demand_forecast

    # Apply pipeline weight to final order
    final_order = pipeline_weight * smoothed_order + (1 - pipeline_weight) * demand_forecast

    # Ensure order is integer and non-negative
    order_amount = max(0, int(round(final_order)))

    return order_amount
