# policy_hash: cfcdd514e550f382d2835811ac86c464cc0f73447263c019143d0c43990389e1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 27
# source_prompt_files: 2
# best_target_performance: 10186.63
# best_prompt_performance: 10186.63
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_074249.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 421.0649070088141  # OPT_PARAM: {"initial": 421.0649070088141, "min": 100, "max": 500, "type": "float"}
    safety_factor = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 0.5, "max": 3.0, "type": "float"}
    demand_smoothing = 0.39059229941129714  # OPT_PARAM: {"initial": 0.39059229941129714, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand variability from pipeline orders
    if len(pipeline_orders) >= 2:
        # Use standard deviation of recent orders as demand variability proxy
        recent_orders = pipeline_orders[:min(3, len(pipeline_orders))]
        if len(recent_orders) > 1:
            mean_order = sum(recent_orders) / len(recent_orders)
            variance = sum((x - mean_order) ** 2 for x in recent_orders) / len(recent_orders)
            std_dev = variance ** 0.5
        else:
            std_dev = 0
    else:
        std_dev = 0

    # Dynamic safety stock based on demand variability
    dynamic_safety = safety_factor * std_dev

    # Smooth adjustment to target
    target_position = base_stock + dynamic_safety

    # Calculate order amount with smoothing
    gap = target_position - inventory_position
    if gap > 0:
        order_amount = max(0, gap * demand_smoothing)
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
