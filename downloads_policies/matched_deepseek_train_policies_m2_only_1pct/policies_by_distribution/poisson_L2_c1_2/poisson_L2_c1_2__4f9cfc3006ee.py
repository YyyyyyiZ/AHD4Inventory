# policy_hash: 4f9cfc3006ee63633d91687ec78bcc23faadff3ca54bf48f06bb110b26a51ee1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1043.76
# best_prompt_performance: 1043.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_222857.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 294.00000005067415  # OPT_PARAM: {"initial": 294.00000005067415, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 100, "type": "float"}
    demand_estimate = 100.1  # OPT_PARAM: {"initial": 100.1, "min": 50, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, target_inventory)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    return order_amount
