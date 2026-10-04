# policy_hash: 6b7a69dd09a3e8aa9fbfd67626a63db114b7ed976bb94d3c43607cf4240c9a8e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 5880.68
# best_prompt_performance: 5880.68
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_071243.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 309.7685451126772  # OPT_PARAM: {"initial": 309.7685451126772, "min": 250, "max": 400, "type": "float"}
    safety_stock = 84.36709493219507  # OPT_PARAM: {"initial": 84.36709493219507, "min": 70, "max": 130, "type": "float"}
    pipeline_factor = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.85, "max": 1.0, "type": "float"}
    smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    demand_estimate = 125.95528654342104  # OPT_PARAM: {"initial": 125.95528654342104, "min": 100, "max": 160, "type": "float"}
    lost_sales_weight = 1.8  # OPT_PARAM: {"initial": 1.8, "min": 1.5, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate pipeline coverage with full factor
    pipeline_coverage = sum(pipeline_orders) * pipeline_factor

    # Dynamic safety stock adjustment based on pipeline
    if len(pipeline_orders) > 0:
        pipeline_ratio = pipeline_orders[0] / (demand_estimate + 1e-6)
        adjusted_safety = safety_stock * (1.0 + 0.3 * max(0, 1.0 - pipeline_ratio))
    else:
        adjusted_safety = safety_stock

    # Calculate target inventory level
    target_inventory = base_stock + adjusted_safety - pipeline_coverage

    # Ensure minimum target based on expected demand with lost sales weight
    min_target = demand_estimate * lost_sales_weight
    target_inventory = max(target_inventory, min_target)

    # Calculate order needed
    order_needed = target_inventory - inventory_position

    # Apply smoothing with dynamic capping
    if order_needed > 0:
        # Dynamic max order based on recent pipeline and demand
        max_order = demand_estimate * 2.2
        capped_order = min(order_needed, max_order)
        smoothed_order = capped_order * smoothing
        order_amount = int(round(max(0, smoothed_order)))
    else:
        order_amount = 0

    return order_amount
