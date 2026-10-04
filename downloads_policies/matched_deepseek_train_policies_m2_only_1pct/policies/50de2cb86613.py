# policy_hash: 50de2cb866130256b8df25a6a39e560e9b4caa7d6bbe10f025b6b0e16334f409
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 5890.6
# best_prompt_performance: 5890.3
# best_rel_error_pct: 0.005093
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_025831.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 141.33362007393262  # OPT_PARAM: {"initial": 141.33362007393262, "min": 100, "max": 300, "type": "float"}
    safety_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.5, "max": 2.5, "type": "float"}
    demand_estimate = 51.72272264709384  # OPT_PARAM: {"initial": 51.72272264709384, "min": 50, "max": 200, "type": "float"}
    smoothing = 0.27600757304258405  # OPT_PARAM: {"initial": 0.27600757304258405, "min": 0.1, "max": 0.8, "type": "float"}
    lost_sales_weight = 1.6861425737781348  # OPT_PARAM: {"initial": 1.6861425737781348, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety factor
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_estimate * lead_time * safety_factor

    # Dynamic order-up-to level based on cost ratio
    # Higher weight on lost sales means we should carry more inventory
    order_up_to = base_stock * lost_sales_weight

    # Ensure minimum coverage of lead time demand
    order_up_to = max(order_up_to, lead_time_demand)

    # Calculate raw order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply stronger smoothing to reduce order volatility
    smoothed_order = smoothing * raw_order + (1 - smoothing) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
