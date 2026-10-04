# policy_hash: 0a83a69ef17c948f60c719273e2163039609479d7eac9cb5ac9e49cb3cdbbe77
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 804.6
# best_prompt_performance: 804.52
# best_rel_error_pct: 0.009943
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_040200.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 420.0000001590838  # OPT_PARAM: {"initial": 420.0000001590838, "min": 380, "max": 480, "type": "float"}
    safety_stock = 75.00000015908383  # OPT_PARAM: {"initial": 75.00000015908383, "min": 60, "max": 120, "type": "float"}
    demand_estimate = 90.92032991283426  # OPT_PARAM: {"initial": 90.92032991283426, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.2, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.0, "type": "float"}

    # Calculate inventory position with full pipeline weight
    inventory_position = on_hand_inventory + sum(pipeline_orders) * pipeline_weight

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Adjust target based on cost ratio: higher lost sales cost requires more inventory
    adjusted_safety_stock = safety_stock * lost_sales_weight

    # Calculate target inventory position
    target_inventory = base_stock + adjusted_safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
