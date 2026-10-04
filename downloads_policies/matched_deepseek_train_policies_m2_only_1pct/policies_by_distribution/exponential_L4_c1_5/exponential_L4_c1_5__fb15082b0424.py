# policy_hash: fb15082b0424de78481b58dc131f7fc2dd28244f645ee93f5def7d1f15aa83df
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 12299.44
# best_prompt_performance: 12299.44
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_043507.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 448.99993377977387  # OPT_PARAM: {"initial": 448.99993377977387, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 0, "max": 500, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 10, "max": 300, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Cap order amount to avoid excessive orders
    max_order = 500.0  # OPT_PARAM: {"initial": 500.0, "min": 100, "max": 1000, "type": "float"}
    order_amount = min(order_amount, max_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
