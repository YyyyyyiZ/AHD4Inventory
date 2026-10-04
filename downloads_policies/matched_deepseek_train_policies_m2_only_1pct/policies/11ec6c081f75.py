# policy_hash: 11ec6c081f75f8d01a5ff8aa866efb9d10b25d6beeb58cbe292c4b6160a51350
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 840.2
# best_prompt_performance: 840.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_040506.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 430.0018988903587  # OPT_PARAM: {"initial": 430.0018988903587, "min": 380, "max": 480, "type": "float"}
    safety_stock = 85.00189889035869  # OPT_PARAM: {"initial": 85.00189889035869, "min": 60, "max": 120, "type": "float"}
    demand_estimate = 95.20871850564434  # OPT_PARAM: {"initial": 95.20871850564434, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.8, "max": 1.2, "type": "float"}
    lost_sales_weight = 1.0366185446846392  # OPT_PARAM: {"initial": 1.0366185446846392, "min": 1.0, "max": 2.0, "type": "float"}

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
