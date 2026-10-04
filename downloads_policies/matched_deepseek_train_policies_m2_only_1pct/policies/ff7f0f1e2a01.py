# policy_hash: ff7f0f1e2a01d3dba67ad3ac03758fb14c5e89bbd69a3a53267353878f5aa75d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 773.45
# best_prompt_performance: 773.45
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260129_000718.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 688.8621484611648  # OPT_PARAM: {"initial": 688.8621484611648, "min": 400, "max": 800, "type": "float"}
    safety_stock = 40.0  # OPT_PARAM: {"initial": 40.0, "min": 20, "max": 100, "type": "float"}
    demand_estimate = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.2, "type": "float"}
    adjustment_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * lead_time

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Use the maximum of base_stock and target_inventory
    order_up_to = max(base_stock, target_inventory)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply adjustment factor
    order_amount = order_amount * adjustment_factor

    # Apply smoothing for large orders
    if order_amount > demand_estimate * 1.2:
        order_amount = demand_estimate * 1.2 + smoothing_factor * (order_amount - demand_estimate * 1.2)

    return order_amount
