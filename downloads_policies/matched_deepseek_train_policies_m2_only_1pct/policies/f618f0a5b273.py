# policy_hash: f618f0a5b2739372d7ac9a641ed2194f0fa726fa1be634ebdb227157a5cbaf5f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 6028.02
# best_prompt_performance: 6028.02
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_095403.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 920.0  # OPT_PARAM: {"initial": 920.0, "min": 700, "max": 1300, "type": "float"}
    demand_forecast = 103.8770079325625  # OPT_PARAM: {"initial": 103.8770079325625, "min": 70, "max": 130, "type": "float"}
    lead_time = 6

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * lead_time

    # Dynamic safety factor based on pipeline coverage
    safety_factor_base = 2.2776020280871037  # OPT_PARAM: {"initial": 2.2776020280871037, "min": 1.2, "max": 2.5, "type": "float"}

    # Adjust safety factor based on pipeline coverage ratio
    pipeline_coverage = sum(pipeline_orders) / (expected_lead_time_demand + 1e-6)
    coverage_adjustment = 0.7107328558466245  # OPT_PARAM: {"initial": 0.7107328558466245, "min": 0.1, "max": 0.8, "type": "float"}

    safety_factor = safety_factor_base * coverage_adjustment

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand * safety_factor
    target_inventory = min(target_inventory, base_stock)

    # Base stock policy with threshold
    order_amount = max(0, target_inventory - inventory_position)

    # Apply order smoothing with dynamic adjustment
    smoothing_base = 0.11639260127217595  # OPT_PARAM: {"initial": 0.11639260127217595, "min": 0.05, "max": 0.4, "type": "float"}

    # Adjust smoothing based on how far from target
    position_ratio = inventory_position / (target_inventory + 1e-6)
    if position_ratio < 0.7:
        smoothing_factor = smoothing_base * 0.8  # Faster adjustment when very low
    elif position_ratio > 1.3:
        smoothing_factor = smoothing_base * 1.2  # Slower adjustment when very high
    else:
        smoothing_factor = smoothing_base

    order_amount = smoothing_factor * order_amount

    # Minimum order threshold to avoid tiny orders
    min_order_threshold = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 40, "type": "float"}
    if order_amount < min_order_threshold and order_amount > 0:
        order_amount = min_order_threshold

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
