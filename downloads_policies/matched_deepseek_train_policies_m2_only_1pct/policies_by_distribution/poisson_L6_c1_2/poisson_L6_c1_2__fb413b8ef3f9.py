# policy_hash: fb413b8ef3f9094fadc39c6c8b967538d9c66d7aa448e795f3053e9d7d43daae
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1170.32
# best_prompt_performance: 1170.32
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260129_000111.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 766.861487547453  # OPT_PARAM: {"initial": 766.861487547453, "min": 400, "max": 900, "type": "float"}
    safety_stock = 75.0  # OPT_PARAM: {"initial": 75.0, "min": 20, "max": 150, "type": "float"}
    demand_estimate = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.2, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate order-up-to level with adjustment
    order_up_to = max(base_stock, target_inventory)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply adjustment factor to reduce over-ordering
    order_amount = order_amount * adjustment_factor

    # Apply smoothing only for large orders
    if order_amount > demand_estimate * 1.5:
        order_amount = demand_estimate * 1.5 + smoothing_factor * (order_amount - demand_estimate * 1.5)

    return order_amount
