# policy_hash: a552b44cb39d0ba89df742cbed9193cf997a17c721d926b72575c2a4f9feb400
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 5888.58
# best_prompt_performance: 5888.58
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_070046.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 318.378464646849  # OPT_PARAM: {"initial": 318.378464646849, "min": 200, "max": 450, "type": "float"}
    safety_stock = 82.61640332168338  # OPT_PARAM: {"initial": 82.61640332168338, "min": 50, "max": 180, "type": "float"}
    pipeline_factor = 0.836376533891012  # OPT_PARAM: {"initial": 0.836376533891012, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 1.0, "type": "float"}
    demand_estimate = 127.13870626642273  # OPT_PARAM: {"initial": 127.13870626642273, "min": 80, "max": 200, "type": "float"}
    lost_sales_weight = 1.6831703781893892  # OPT_PARAM: {"initial": 1.6831703781893892, "min": 1.2, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on lost-sales cost ratio
    adjusted_base = base_stock * lost_sales_weight / 2.0

    # Calculate pipeline coverage with stronger discount
    pipeline_coverage = sum(pipeline_orders) * pipeline_factor

    # Calculate target inventory level
    # More aggressive safety stock for high lost-sales cost
    target_inventory = adjusted_base + safety_stock - pipeline_coverage

    # Dynamic minimum target based on expected demand
    min_target = demand_estimate * 2.0
    target_inventory = max(target_inventory, min_target)

    # Calculate order needed
    order_needed = target_inventory - inventory_position

    # Apply smoothing with demand-based capping
    if order_needed > 0:
        # Cap order based on expected demand and current pipeline
        max_order = max(demand_estimate * 2.5, sum(pipeline_orders) * 0.7)
        capped_order = min(order_needed, max_order)
        smoothed_order = capped_order * smoothing
        order_amount = int(round(smoothed_order))
    else:
        order_amount = 0

    return order_amount
