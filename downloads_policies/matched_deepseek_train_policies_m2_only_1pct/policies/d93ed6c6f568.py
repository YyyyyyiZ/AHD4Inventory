# policy_hash: d93ed6c6f5687b718b19013a072fe9cef304bcd0940091b82c0be6e8d1a39f95
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 6159.27
# best_prompt_performance: 6155.9
# best_rel_error_pct: 0.054714
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_091910.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 110.62121435155537  # OPT_PARAM: {"initial": 110.62121435155537, "min": 100, "max": 400, "type": "float"}
    demand_multiplier = 0.8494939589154904  # OPT_PARAM: {"initial": 0.8494939589154904, "min": 0.8, "max": 2.0, "type": "float"}
    pipeline_weight = 1.4968629274642564  # OPT_PARAM: {"initial": 1.4968629274642564, "min": 0.1, "max": 1.5, "type": "float"}
    safety_stock = 14.956759513833592  # OPT_PARAM: {"initial": 14.956759513833592, "min": 10, "max": 150, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 50, "type": "int"}

    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted average of pipeline orders
    if lead_time > 0 and sum(pipeline_orders) > 0:
        # Simple exponential smoothing weights (recent gets more weight)
        weights = [pipeline_weight ** i for i in range(lead_time)]
        weights.reverse()
        weighted_sum = sum(w * q for w, q in zip(weights, pipeline_orders))
        weight_sum = sum(weights)
        estimated_demand = weighted_sum / weight_sum
    else:
        estimated_demand = 0

    # Calculate expected demand during lead time with multiplier
    expected_lead_time_demand = estimated_demand * lead_time * demand_multiplier

    # Calculate target inventory position with safety stock
    target_inventory = base_stock + expected_lead_time_demand + safety_stock

    # Calculate order amount
    order_amount = max(min_order, target_inventory - inventory_position)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
