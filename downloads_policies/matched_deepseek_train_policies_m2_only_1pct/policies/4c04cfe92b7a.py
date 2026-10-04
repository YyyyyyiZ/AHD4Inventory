# policy_hash: 4c04cfe92b7adbd56abfaed842297e7b89ce65af9c3c1f671ae1bb30e4db1b36
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 4455.42
# best_prompt_performance: 4456.34
# best_rel_error_pct: 0.020649
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_230343.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 536.1039776106899  # OPT_PARAM: {"initial": 536.1039776106899, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 52.15212281052027  # OPT_PARAM: {"initial": 52.15212281052027, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.2893125403368116  # OPT_PARAM: {"initial": 0.2893125403368116, "min": 0.1, "max": 0.9, "type": "float"}
    lead_time = 6  # OPT_PARAM: {"initial": 6, "min": 1, "max": 12, "type": "int"}
    demand_forecast_factor = 0.9241022996760959  # OPT_PARAM: {"initial": 0.9241022996760959, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using pipeline orders as indicator
    upcoming_demand_estimate = demand_forecast_factor * sum(pipeline_orders[:lead_time//2]) / max(1, len(pipeline_orders[:lead_time//2]))

    # Adjust base stock based on upcoming demand estimate
    adjusted_base_stock = base_stock + upcoming_demand_estimate

    # Calculate expected shortfall with smoothing
    expected_shortfall = max(0, adjusted_base_stock - inventory_position)

    # Add safety stock adjustment
    adjusted_shortfall = expected_shortfall + safety_stock

    # Apply smoothing to avoid large order swings
    order_amount = max(0, smoothing_factor * adjusted_shortfall)

    # Round to nearest integer for practical ordering
    order_amount = int(round(order_amount))

    return order_amount
