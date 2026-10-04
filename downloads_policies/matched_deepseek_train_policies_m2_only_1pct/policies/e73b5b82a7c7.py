# policy_hash: e73b5b82a7c7c3e7958c9bf7c6ef048327fcc87c8b0a03c64110b600e81876bc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 767.24
# best_prompt_performance: 767.23
# best_rel_error_pct: 0.001303
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260129_000953.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 745.9180740910386  # OPT_PARAM: {"initial": 745.9180740910386, "min": 500, "max": 750, "type": "float"}
    safety_stock = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 30, "max": 90, "type": "float"}
    demand_estimate = 95.2273955801629  # OPT_PARAM: {"initial": 95.2273955801629, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.1, "type": "float"}
    adjustment_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * lead_time

    # Calculate target inventory level with more weight on safety stock
    target_inventory = expected_lead_time_demand + safety_stock

    # Use weighted combination instead of max
    order_up_to = 0.7 * base_stock + 0.3 * target_inventory

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply adjustment factor
    order_amount = order_amount * adjustment_factor

    # Apply smoothing for large orders with tighter threshold
    if order_amount > demand_estimate:
        order_amount = demand_estimate + smoothing_factor * (order_amount - demand_estimate)

    return order_amount
