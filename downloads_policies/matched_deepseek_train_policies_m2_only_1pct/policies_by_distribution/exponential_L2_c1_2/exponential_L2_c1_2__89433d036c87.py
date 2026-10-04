# policy_hash: 89433d036c8740218f15e95191b054541fbbcff86cce03fa17e927bb77b071e7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 5878.44
# best_prompt_performance: 5878.64
# best_rel_error_pct: 0.003402
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_070326.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 300.1548492180182  # OPT_PARAM: {"initial": 300.1548492180182, "min": 200, "max": 450, "type": "float"}
    safety_stock = 69.33129485503127  # OPT_PARAM: {"initial": 69.33129485503127, "min": 50, "max": 180, "type": "float"}
    pipeline_factor = 0.9504499444033159  # OPT_PARAM: {"initial": 0.9504499444033159, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing = 0.3312764288833672  # OPT_PARAM: {"initial": 0.3312764288833672, "min": 0.2, "max": 1.0, "type": "float"}
    demand_estimate = 135.0  # OPT_PARAM: {"initial": 135.0, "min": 80, "max": 200, "type": "float"}
    lost_sales_weight = 1.2943392817327564  # OPT_PARAM: {"initial": 1.2943392817327564, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on cost ratio (p/h = 2)
    # Higher lost sales weight increases target inventory
    adjusted_base = base_stock * (1 + (lost_sales_weight - 1) * 0.2)

    # Calculate pipeline coverage with stronger discount
    pipeline_coverage = sum(pipeline_orders) * pipeline_factor

    # Target inventory: adjusted base + safety - pipeline coverage
    target_inventory = adjusted_base + safety_stock - pipeline_coverage

    # Ensure minimum target is proportional to expected demand
    min_target = demand_estimate * 1.5
    target_inventory = max(target_inventory, min_target)

    # Calculate order needed
    order_needed = target_inventory - inventory_position

    # Apply smoothing with demand-based capping
    if order_needed > 0:
        # Cap order based on expected demand and current shortage
        max_order = max(demand_estimate * 2.5, order_needed * 0.8)
        smoothed_order = min(order_needed, max_order) * smoothing
        order_amount = int(round(smoothed_order))
    else:
        order_amount = 0

    return order_amount
