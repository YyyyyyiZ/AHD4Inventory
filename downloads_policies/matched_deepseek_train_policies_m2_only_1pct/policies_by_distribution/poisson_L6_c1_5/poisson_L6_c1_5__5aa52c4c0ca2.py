# policy_hash: 5aa52c4c0ca2f967f4dcc3e4eb04b9899ad624e9f4ffafd7c63c3090486453bf
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1637.42
# best_prompt_performance: 1636.74
# best_rel_error_pct: 0.041529
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_020022.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 850.0  # OPT_PARAM: {"initial": 850.0, "min": 700, "max": 1000, "type": "float"}
    demand_estimate = 90.82660868442447  # OPT_PARAM: {"initial": 90.82660868442447, "min": 90, "max": 115, "type": "float"}
    safety_factor = 1.213284758726767  # OPT_PARAM: {"initial": 1.213284758726767, "min": 1.2, "max": 2.5, "type": "float"}
    max_order_cap = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 120, "max": 250, "type": "float"}
    min_order_cap = 14.405502988649722  # OPT_PARAM: {"initial": 14.405502988649722, "min": 5, "max": 40, "type": "float"}
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
