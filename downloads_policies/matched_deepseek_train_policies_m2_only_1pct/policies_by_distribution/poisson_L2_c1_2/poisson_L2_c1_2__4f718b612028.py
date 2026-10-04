# policy_hash: 4f718b612028bea265d8fa139ab4712de03a739f8b62a62e368634c97d12e9da
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 716.8
# best_prompt_performance: 716.64
# best_rel_error_pct: 0.022321
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_224630.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 200.6342082321934  # OPT_PARAM: {"initial": 200.6342082321934, "min": 200, "max": 350, "type": "float"}
    safety_stock = 10.633642004053945  # OPT_PARAM: {"initial": 10.633642004053945, "min": 10, "max": 60, "type": "float"}
    demand_forecast = 97.73628934627966  # OPT_PARAM: {"initial": 97.73628934627966, "min": 90, "max": 110, "type": "float"}
    lead_time_factor = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 0.8, "max": 1.5, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    lost_sales_weight = 3.0  # OPT_PARAM: {"initial": 3.0, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Dynamic safety stock adjustment based on pipeline variability
    if len(pipeline_orders) > 0:
        pipeline_std = max(1.0, sum(abs(p - demand_forecast) for p in pipeline_orders) / len(pipeline_orders))
        adjusted_safety = safety_stock * (1.0 + pipeline_std / (2 * demand_forecast))
    else:
        adjusted_safety = safety_stock

    # Calculate order-up-to level with lost-sales cost consideration
    order_up_to = base_stock + adjusted_safety * lead_time_factor * lost_sales_weight

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with demand forecast adjustment
    if raw_order > 0:
        # Blend between base order and demand forecast with stronger smoothing
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
        # Ensure order doesn't drop below forecast when inventory is low
        if inventory_position < base_stock:
            smoothed_order = max(smoothed_order, demand_forecast * 0.8)
    else:
        smoothed_order = 0

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
