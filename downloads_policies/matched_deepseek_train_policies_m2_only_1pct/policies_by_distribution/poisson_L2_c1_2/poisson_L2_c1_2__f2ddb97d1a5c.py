# policy_hash: f2ddb97d1a5c4ee65c7edc6869b9d72121ee628398a01d66ff35ba9d0f5e8931
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 994.08
# best_prompt_performance: 994.08
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_022926.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 380.0  # OPT_PARAM: {"initial": 380.0, "min": 300, "max": 450, "type": "float"}
    safety_stock = 100.08859484643696  # OPT_PARAM: {"initial": 100.08859484643696, "min": 100, "max": 180, "type": "float"}
    demand_estimate = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 110, "type": "float"}
    lead_time_demand_factor = 1.3  # OPT_PARAM: {"initial": 1.3, "min": 1.0, "max": 1.3, "type": "float"}
    smoothing_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.8, "max": 1.0, "type": "float"}
    lost_sales_weight = 1.8683905675410382  # OPT_PARAM: {"initial": 1.8683905675410382, "min": 1.5, "max": 2.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders) * lead_time_demand_factor

    # Adjust safety stock based on cost ratio (p/h = 2)
    # Higher lost_sales_weight increases target inventory when facing stockouts
    adjusted_safety_stock = safety_stock * lost_sales_weight

    # Calculate target inventory level
    target_inventory = expected_demand_during_leadtime + adjusted_safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - net_inventory)

    # Apply smoothing
    smoothed_order = smoothing_factor * raw_order

    # Apply base stock policy with tighter bounds
    if net_inventory < base_stock:
        max_order = base_stock - net_inventory
        smoothed_order = min(smoothed_order, max_order)
    else:
        smoothed_order = 0

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
