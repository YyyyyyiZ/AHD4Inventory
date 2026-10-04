# policy_hash: 6438727a1dfa3693ccdee0f60358ef19dee218a33d39f93483a7ea3282e881aa
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 6071.2
# best_prompt_performance: 6070.76
# best_rel_error_pct: 0.007247
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_014824.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 420.0  # OPT_PARAM: {"initial": 420.0, "min": 350, "max": 550, "type": "float"}
    safety_stock = 173.97615492145357  # OPT_PARAM: {"initial": 173.97615492145357, "min": 120, "max": 250, "type": "float"}
    demand_estimate = 119.01207462790403  # OPT_PARAM: {"initial": 119.01207462790403, "min": 100, "max": 150, "type": "float"}
    pipeline_weight = 0.6626935898645728  # OPT_PARAM: {"initial": 0.6626935898645728, "min": 0.3, "max": 1.0, "type": "float"}
    adjustment_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    lost_sales_weight = 1.6591728663023662  # OPT_PARAM: {"initial": 1.6591728663023662, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety factor
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_estimate * lead_time

    # Calculate effective pipeline with weighting
    effective_pipeline = sum(p * (pipeline_weight ** (i + 1)) for i, p in enumerate(pipeline_orders))

    # Adjust safety stock based on lost sales cost weight
    adjusted_safety_stock = safety_stock * lost_sales_weight

    # Calculate target inventory level
    target_level = max(base_stock, lead_time_demand + adjusted_safety_stock - effective_pipeline)

    # Calculate order amount with smoothing
    raw_order = target_level - inventory_position
    order_amount = max(0, raw_order) * adjustment_smoothing

    # Add small buffer for high demand periods
    if raw_order > demand_estimate * 2:
        order_amount = order_amount * 1.2

    # Ensure non-negative and round to integer
    order_amount = max(0, order_amount)
    order_amount = int(round(order_amount))

    return order_amount
