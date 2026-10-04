# policy_hash: 17b07f4b1eda0b0ee62b276596da7f4a48d60912c706780b08d14f6c75ebfff7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2764.92
# best_prompt_performance: 2776.1
# best_rel_error_pct: 0.404352
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r9/prompt_for_code/m2_20260129_221323.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 899.9946750173914  # OPT_PARAM: {"initial": 899.9946750173914, "min": 800, "max": 1000, "type": "float"}
    demand_forecast = 103.78221095626039  # OPT_PARAM: {"initial": 103.78221095626039, "min": 95, "max": 105, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_forecast * len(pipeline_orders)

    # Calculate pipeline coverage
    pipeline_coverage = sum(pipeline_orders) / expected_demand_during_leadtime if expected_demand_during_leadtime > 0 else 1.0

    # Dynamic adjustment based on pipeline coverage
    if pipeline_coverage < 0.9:  # OPT_PARAM: {"initial": 0.9, "min": 0.8, "max": 1.0, "type": "float"}
        adjustment = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.2, "type": "float"}
    elif pipeline_coverage > 1.1:  # OPT_PARAM: {"initial": 1.1, "min": 1.0, "max": 1.2, "type": "float"}
        adjustment = 0.95  # OPT_PARAM: {"initial": 0.95, "min": 0.8, "max": 1.0, "type": "float"}
    else:
        adjustment = 1.0

    # Calculate target inventory position
    target_position = base_stock * adjustment

    # Calculate order amount
    order_needed = target_position - inventory_position

    # Apply smoothing
    smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    smoothed_order = max(0, order_needed * smoothing)

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
