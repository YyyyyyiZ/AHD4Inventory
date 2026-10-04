# policy_hash: fa49de62c40afb22cf32b756e7baada78ebfadd4db9648b5c7cbdcbd49958f9f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 5881.36
# best_prompt_performance: 5881.36
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_030417.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 142.0  # OPT_PARAM: {"initial": 142.0, "min": 80, "max": 300, "type": "float"}
    safety_factor = 2.500271567158064  # OPT_PARAM: {"initial": 2.500271567158064, "min": 0.5, "max": 3.0, "type": "float"}
    demand_estimate = 59.1902700506081  # OPT_PARAM: {"initial": 59.1902700506081, "min": 50, "max": 200, "type": "float"}
    smoothing = 0.208942462435761  # OPT_PARAM: {"initial": 0.208942462435761, "min": 0.1, "max": 1.0, "type": "float"}
    min_order = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_estimate * lead_time

    # Calculate safety stock based on demand variability
    safety_stock = safety_factor * demand_estimate

    # Dynamic order-up-to level that adjusts with pipeline
    order_up_to = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.0, "max": 0.5, "type": "float"}

    # Ensure minimum coverage
    order_up_to = max(order_up_to, lead_time_demand + safety_stock)

    # Calculate raw order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with minimum order threshold
    smoothed_order = smoothing * raw_order + (1 - smoothing) * demand_estimate
    smoothed_order = max(smoothed_order, min_order)

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
