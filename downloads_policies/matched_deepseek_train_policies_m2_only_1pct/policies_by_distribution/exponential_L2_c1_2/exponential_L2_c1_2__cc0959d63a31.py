# policy_hash: cc0959d63a310eedb9981a51f0d8654c353d09313ac194d1eb2186d4f209af3c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 5877.24
# best_prompt_performance: 5877.24
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_071008.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 308.5918440606735  # OPT_PARAM: {"initial": 308.5918440606735, "min": 250, "max": 400, "type": "float"}
    safety_stock = 74.55199970219371  # OPT_PARAM: {"initial": 74.55199970219371, "min": 60, "max": 150, "type": "float"}
    pipeline_factor = 0.9451036046383914  # OPT_PARAM: {"initial": 0.9451036046383914, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}
    demand_estimate = 125.0  # OPT_PARAM: {"initial": 125.0, "min": 90, "max": 180, "type": "float"}
    lost_sales_weight = 1.3775835794084215  # OPT_PARAM: {"initial": 1.3775835794084215, "min": 1.2, "max": 2.5, "type": "float"}
    pipeline_boost = 0.09468681649228573  # OPT_PARAM: {"initial": 0.09468681649228573, "min": 0.05, "max": 0.3, "type": "float"}
    shortage_factor = 1.5069618380558232  # OPT_PARAM: {"initial": 1.5069618380558232, "min": 1.2, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on cost ratio with stronger response
    adjusted_base = base_stock * (1 + (lost_sales_weight - 1) * 0.3)

    # Calculate pipeline coverage with boost for upcoming arrivals
    pipeline_coverage = sum(pipeline_orders) * pipeline_factor
    pipeline_boost_amount = sum(pipeline_orders) * pipeline_boost

    # Target inventory: adjusted base + safety - pipeline coverage + pipeline boost
    target_inventory = adjusted_base + safety_stock - pipeline_coverage + pipeline_boost_amount

    # Dynamic minimum target based on expected demand and current pipeline
    min_target = demand_estimate * 1.8 + pipeline_boost_amount
    target_inventory = max(target_inventory, min_target)

    # Calculate order needed
    order_needed = target_inventory - inventory_position

    # Apply smoothing with dynamic capping
    if order_needed > 0:
        # More aggressive ordering when facing shortages
        current_shortage = max(0, demand_estimate - (on_hand_inventory + pipeline_orders[0]))
        max_order = max(demand_estimate * shortage_factor,
                       order_needed * 0.9,
                       current_shortage * 1.5)
        smoothed_order = min(order_needed, max_order) * smoothing
        order_amount = int(round(smoothed_order))
    else:
        order_amount = 0

    return order_amount
