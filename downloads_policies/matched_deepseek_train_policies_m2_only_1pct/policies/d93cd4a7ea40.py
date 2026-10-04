# policy_hash: d93cd4a7ea408d9cbdab938ac4e7379805dc2fc0700b9fa1bfa4009621595c49
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 4603.6
# best_prompt_performance: 4601.96
# best_rel_error_pct: 0.035624
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_230718.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 639.2815488983996  # OPT_PARAM: {"initial": 639.2815488983996, "min": 400, "max": 900, "type": "float"}
    safety_stock = 20.10550499353515  # OPT_PARAM: {"initial": 20.10550499353515, "min": 20, "max": 150, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    lead_time_demand_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate lead time demand using pipeline orders as indicator
    # Use average of recent pipeline orders as demand estimate
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
        avg_recent_order = sum(recent_orders) / len(recent_orders)
        lead_time_demand_estimate = avg_recent_order * len(pipeline_orders) * lead_time_demand_factor
    else:
        lead_time_demand_estimate = 0

    # Dynamic base stock adjustment based on lead time demand
    dynamic_base_stock = base_stock + 0.3 * lead_time_demand_estimate

    # Calculate expected shortfall
    expected_shortfall = max(0, dynamic_base_stock - inventory_position)

    # Add safety stock with adjustment for current inventory level
    if on_hand_inventory < safety_stock:
        safety_adjustment = safety_stock * (1.0 - on_hand_inventory / safety_stock)
    else:
        safety_adjustment = 0

    adjusted_shortfall = expected_shortfall + safety_adjustment

    # Apply smoothing with minimum order threshold
    raw_order = smoothing_factor * adjusted_shortfall

    # Add minimum order quantity when shortfall is significant
    if adjusted_shortfall > 50:
        raw_order = max(raw_order, 0.3 * adjusted_shortfall)

    order_amount = max(0, raw_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
