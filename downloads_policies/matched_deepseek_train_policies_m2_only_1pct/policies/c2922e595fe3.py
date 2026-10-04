# policy_hash: c2922e595fe3753a71c6d3937b766793307002cd0f131a181e5778c3b3698581
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 10686.54
# best_prompt_performance: 10686.54
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_231325.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 289.1988365189299  # OPT_PARAM: {"initial": 289.1988365189299, "min": 100, "max": 500, "type": "float"}
    safety_stock = 55.62640348308868  # OPT_PARAM: {"initial": 55.62640348308868, "min": 20, "max": 150, "type": "float"}
    demand_forecast_factor = 0.6718301925842636  # OPT_PARAM: {"initial": 0.6718301925842636, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple target calculation without complex pipeline weighting
    target = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target - inventory_position)

    # Apply demand-based adjustment
    if order_amount > 0:
        # Use simpler smoothing based on forecast factor
        order_amount = demand_forecast_factor * order_amount + (1 - demand_forecast_factor) * (base_stock / (len(pipeline_orders) + 1))

    # Ensure integer output
    return order_amount
