# policy_hash: 9f86e3b6eb79a3e3dee119d5b0bdd1eaaca508b97b3375967c1f935c5f18f2e7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 4708.46
# best_prompt_performance: 4705.62
# best_rel_error_pct: 0.060317
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_013555.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 400.0  # OPT_PARAM: {"initial": 400.0, "min": 400, "max": 900, "type": "float"}
    safety_stock = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 60, "max": 200, "type": "float"}
    demand_forecast = 106.19481652245614  # OPT_PARAM: {"initial": 106.19481652245614, "min": 90, "max": 140, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.2, "type": "float"}
    pipeline_weight = 0.95  # OPT_PARAM: {"initial": 0.95, "min": 0.8, "max": 1.0, "type": "float"}
    lost_sales_weight = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 2.5, "type": "float"}
    holding_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.2, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety stock
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Adjust safety stock based on cost ratio (p/h = 2)
    # Higher lost sales cost means we need more safety stock
    adjusted_safety_stock = safety_stock * lost_sales_weight / (lost_sales_weight + holding_weight)

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + adjusted_safety_stock

    # Use base_stock as upper bound, target_inventory as lower bound
    order_up_to = max(base_stock, target_inventory)

    # Calculate base order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply minimal smoothing only
    if len(pipeline_orders) > 0 and smoothing_factor > 0:
        # Simple exponential smoothing of pipeline
        recent_pipeline = pipeline_orders[-1] if len(pipeline_orders) > 0 else 0
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_pipeline
        order_amount = max(0, smoothed_order)

    # Round to nearest integer (practical implementation)
    order_amount = int(round(order_amount))

    return order_amount
