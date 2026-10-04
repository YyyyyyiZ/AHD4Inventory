# policy_hash: c231d4e5aed0d2e4b2918dea43c51b6056d788cffc2f94ebcc74864a4da69cf9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 814.04
# best_prompt_performance: 814.92
# best_rel_error_pct: 0.108103
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_040655.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 420.0000158041727  # OPT_PARAM: {"initial": 420.0000158041727, "min": 380, "max": 480, "type": "float"}
    safety_stock = 60.44493451040675  # OPT_PARAM: {"initial": 60.44493451040675, "min": 60, "max": 120, "type": "float"}
    demand_estimate = 90.2531844368574  # OPT_PARAM: {"initial": 90.2531844368574, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.2, "type": "float"}
    lost_sales_weight = 1.0223885581110084  # OPT_PARAM: {"initial": 1.0223885581110084, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position (full pipeline value)
    inventory_position = on_hand_inventory + sum(pipeline_orders) * pipeline_weight

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Dynamic safety stock adjustment based on cost ratio
    adjusted_safety = safety_stock * lost_sales_weight

    # Calculate target inventory position
    target_inventory = base_stock + adjusted_safety

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
