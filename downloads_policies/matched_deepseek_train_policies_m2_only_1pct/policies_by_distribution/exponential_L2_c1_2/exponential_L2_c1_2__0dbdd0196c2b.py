# policy_hash: 0dbdd0196c2b85f2c03c023e005a4697f8f119b1c7f01b0cca3aad73cc4470cd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 5897.18
# best_prompt_performance: 5896.72
# best_rel_error_pct: 0.007800
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_065824.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 275.8024032223387  # OPT_PARAM: {"initial": 275.8024032223387, "min": 150, "max": 400, "type": "float"}
    safety_stock = 70.50240322233742  # OPT_PARAM: {"initial": 70.50240322233742, "min": 30, "max": 150, "type": "float"}
    pipeline_factor = 0.9400533911173398  # OPT_PARAM: {"initial": 0.9400533911173398, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing = 0.40877256951750923  # OPT_PARAM: {"initial": 0.40877256951750923, "min": 0.3, "max": 1.0, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 50, "max": 250, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate expected demand using historical average
    expected_demand = demand_estimate

    # Calculate pipeline coverage
    pipeline_coverage = sum(pipeline_orders) * pipeline_factor

    # Calculate target inventory level
    # Base stock + safety stock adjusted for pipeline coverage
    target_inventory = base_stock + safety_stock - pipeline_coverage

    # Ensure minimum target
    min_target = base_stock * 0.5
    target_inventory = max(target_inventory, min_target)

    # Calculate order needed
    order_needed = target_inventory - inventory_position

    # Apply smoothing and ensure non-negative
    if order_needed > 0:
        # Cap order to reasonable multiple of expected demand
        max_order = expected_demand * 3.0
        smoothed_order = min(order_needed, max_order) * smoothing
        order_amount = int(round(smoothed_order))
    else:
        order_amount = 0

    return order_amount
