# policy_hash: 930ad6b86f0f1cfbb4f169d8957b34cd4af6249693736e711d4417379a43d6ab
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2670.1
# best_prompt_performance: 2670.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_073456.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.3999999999995  # OPT_PARAM: {"initial": 450.3999999999995, "min": 300, "max": 600, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 20, "max": 150, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 80, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Add base stock adjustment for stability
    base_stock_adjustment = max(0, base_stock - inventory_position - order_amount)
    order_amount += base_stock_adjustment * 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.5, "type": "float"}

    # Round to nearest integer (orders should be integer quantities)
    order_amount = int(round(order_amount))

    return order_amount
