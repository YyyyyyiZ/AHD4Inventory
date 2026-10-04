# policy_hash: 9d56c79ca70f0f962ef617fcccaee6e83099e2c0691b411aa7112cd03e9e9ee4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2188.06
# best_prompt_performance: 2173.04
# best_rel_error_pct: 0.686453
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_015751.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 820.0  # OPT_PARAM: {"initial": 820.0, "min": 700, "max": 950, "type": "float"}
    demand_estimate = 97.39607130372517  # OPT_PARAM: {"initial": 97.39607130372517, "min": 90, "max": 110, "type": "float"}
    safety_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.0, "type": "float"}
    max_order_cap = 162.89850687583095  # OPT_PARAM: {"initial": 162.89850687583095, "min": 120, "max": 250, "type": "float"}
    min_order_cap = 13.92161243590689  # OPT_PARAM: {"initial": 13.92161243590689, "min": 5, "max": 30, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety factor
    expected_lead_time_demand = demand_estimate * lead_time
    safety_stock = safety_factor * demand_estimate * (lead_time ** 0.5)

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
