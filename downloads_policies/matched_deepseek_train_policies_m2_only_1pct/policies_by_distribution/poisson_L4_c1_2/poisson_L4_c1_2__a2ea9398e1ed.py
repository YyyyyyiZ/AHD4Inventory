# policy_hash: a2ea9398e1ed7f888b7b03e70d10a0d763ba79563af7606ced05f810368880e8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 60
# source_prompt_files: 1
# best_target_performance: 737.62
# best_prompt_performance: 737.62
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_025148.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 491.7274592879092  # OPT_PARAM: {"initial": 491.7274592879092, "min": 400, "max": 600, "type": "float"}
    safety_stock = 30.0  # OPT_PARAM: {"initial": 30.0, "min": 20, "max": 50, "type": "float"}
    lead_time = 4

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Simple order-up-to policy
    order_up_to = base_stock

    # Calculate order amount
    order_amount = max(0, order_up_to - net_inventory)

    # Apply ordering limits
    max_order = 96.74262030961454  # OPT_PARAM: {"initial": 96.74262030961454, "min": 80, "max": 150, "type": "float"}
    min_order = 7.362452979883932  # OPT_PARAM: {"initial": 7.362452979883932, "min": 0, "max": 20, "type": "float"}

    # Cap the order amount
    if order_amount > max_order:
        order_amount = max_order
    elif order_amount < min_order:
        order_amount = min_order

    # Round to nearest integer
    return order_amount
