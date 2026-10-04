# policy_hash: fd87533d1d808ebabd6b681e4474dce32a5fb00b8259b6c92f4a141a15b42ebf
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1960.08
# best_prompt_performance: 1954.56
# best_rel_error_pct: 0.281621
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_015408.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 750.0  # OPT_PARAM: {"initial": 750.0, "min": 600, "max": 900, "type": "float"}
    demand_estimate = 116.99646528069206  # OPT_PARAM: {"initial": 116.99646528069206, "min": 80, "max": 120, "type": "float"}
    safety_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.5, "type": "float"}
    max_order_cap = 141.49880215396  # OPT_PARAM: {"initial": 141.49880215396, "min": 100, "max": 200, "type": "float"}
    min_order_cap = 20.32053058566856  # OPT_PARAM: {"initial": 20.32053058566856, "min": 10, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety factor
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)
    safety_stock = safety_factor * demand_estimate

    # Calculate target inventory position
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate base order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply order caps
    order_amount = min(order_amount, max_order_cap)

    # Apply minimum order threshold
    if order_amount > 0 and order_amount < min_order_cap:
        order_amount = min_order_cap

    # Ensure integer output
    return order_amount
