# policy_hash: ea1c9c13f629665190f1d181a4ffc7f4d80ea1835c591f82c68a896ea4a550d7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 6097.85
# best_prompt_performance: 6099.18
# best_rel_error_pct: 0.021811
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_014239.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 413.12552380103216  # OPT_PARAM: {"initial": 413.12552380103216, "min": 350, "max": 550, "type": "float"}
    safety_stock = 196.23581642402632  # OPT_PARAM: {"initial": 196.23581642402632, "min": 150, "max": 300, "type": "float"}
    demand_estimate = 100.02297563592289  # OPT_PARAM: {"initial": 100.02297563592289, "min": 100, "max": 130, "type": "float"}
    pipeline_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.9, "type": "float"}
    adjustment_smoothing = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate effective pipeline (weighted sum, more weight on recent orders)
    weights = [pipeline_weight ** (len(pipeline_orders) - i - 1) for i in range(len(pipeline_orders))]
    effective_pipeline = sum(p * w for p, w in zip(pipeline_orders, weights))

    # Calculate target inventory level
    target_level = max(base_stock, lead_time_demand + safety_stock - effective_pipeline)

    # Calculate order amount with smoothing
    raw_order = target_level - inventory_position
    order_amount = raw_order * adjustment_smoothing

    # Ensure non-negative and round to integer
    order_amount = max(0, order_amount)
    order_amount = int(round(order_amount))

    return order_amount
