# policy_hash: 218960970a555aa980452aa0d9da8812c3dd60eebfc0b604081988a432c550dc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 6923.42
# best_prompt_performance: 6926.86
# best_rel_error_pct: 0.049686
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_091642.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 100.00407228382791  # OPT_PARAM: {"initial": 100.00407228382791, "min": 100, "max": 800, "type": "float"}
    demand_multiplier = 0.8662473256242716  # OPT_PARAM: {"initial": 0.8662473256242716, "min": 0.5, "max": 2.5, "type": "float"}
    pipeline_weight = 1.4769947574137747  # OPT_PARAM: {"initial": 1.4769947574137747, "min": 0.1, "max": 1.5, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 50, "type": "int"}

    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using pipeline information
    # Use weighted average of pipeline orders as demand estimate
    if lead_time > 0:
        # Give more weight to recent orders
        weights = [pipeline_weight ** i for i in range(lead_time)]
        weights.reverse()  # Most recent gets highest weight
        weighted_sum = sum(w * q for w, q in zip(weights, pipeline_orders))
        weight_sum = sum(weights)
        estimated_demand = weighted_sum / weight_sum if weight_sum > 0 else 0
    else:
        estimated_demand = 0

    # Calculate expected demand during lead time
    expected_lead_time_demand = estimated_demand * lead_time * demand_multiplier

    # Calculate target inventory position
    target_inventory = base_stock + expected_lead_time_demand

    # Calculate order amount
    order_amount = max(min_order, target_inventory - inventory_position)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
