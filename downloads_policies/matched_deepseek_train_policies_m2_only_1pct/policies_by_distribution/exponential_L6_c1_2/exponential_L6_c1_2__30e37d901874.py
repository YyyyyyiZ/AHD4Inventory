# policy_hash: 30e37d9018741ae62c9fc5488b4c6777048f8aa60336db785f5274d5826230d4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 6078.3
# best_prompt_performance: 6078.3
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_095218.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 805.1999999998689  # OPT_PARAM: {"initial": 805.1999999998689, "min": 600, "max": 1200, "type": "float"}
    demand_forecast = 105.0  # OPT_PARAM: {"initial": 105.0, "min": 80, "max": 140, "type": "float"}
    lead_time = 6

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * lead_time

    # Safety stock with adjusted factor
    safety_factor = 2.2  # OPT_PARAM: {"initial": 2.2, "min": 1.5, "max": 3.5, "type": "float"}

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand * safety_factor
    target_inventory = min(target_inventory, base_stock)

    # Base stock policy
    order_amount = max(0, target_inventory - inventory_position)

    # Apply order smoothing
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    order_amount = smoothing_factor * order_amount

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
