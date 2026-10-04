# policy_hash: 5496ddbaee0331f661d17114674d6bff98901d4cb4c2f724366fa8d031ee1d6d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 20
# source_prompt_files: 1
# best_target_performance: 6377.9
# best_prompt_performance: 6377.62
# best_rel_error_pct: 0.004390
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_013150.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 319.9954038917547  # OPT_PARAM: {"initial": 319.9954038917547, "min": 200, "max": 450, "type": "float"}
    safety_stock = 110.60384928816433  # OPT_PARAM: {"initial": 110.60384928816433, "min": 80, "max": 200, "type": "float"}
    demand_estimate = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 80, "max": 150, "type": "float"}
    pipeline_weight = 0.6899218218343437  # OPT_PARAM: {"initial": 0.6899218218343437, "min": 0.5, "max": 1.0, "type": "float"}
    adjustment_smoothing = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety factor
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_estimate * lead_time

    # Adjust safety stock based on cost ratio (p/h = 2)
    # Higher lost sales cost suggests more aggressive safety stock
    adjusted_safety = safety_stock * lost_sales_weight

    # Calculate effective pipeline (weighted sum)
    # Give more weight to imminent arrivals
    weights = [pipeline_weight ** (lead_time - i) for i in range(lead_time)]
    effective_pipeline = sum(p * w for p, w in zip(pipeline_orders, weights))

    # Calculate target inventory level
    # More aggressive target to reduce lost sales
    target_level = max(base_stock, lead_time_demand + adjusted_safety - effective_pipeline * 0.8)

    # Calculate order amount with less smoothing for faster response
    raw_order = target_level - inventory_position
    order_amount = raw_order * adjustment_smoothing

    # Ensure non-negative and round to integer
    order_amount = max(0, order_amount)
    order_amount = int(round(order_amount))

    return order_amount
