# policy_hash: 96df9251cbdca1fa3e3aa83760e279e1bec874f62e0ad40747f0b6b49b97eb66
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 30
# source_prompt_files: 1
# best_target_performance: 5539.37
# best_prompt_performance: 5539.37
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_002106.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 508.9684522068759  # OPT_PARAM: {"initial": 508.9684522068759, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 25.01628206523205  # OPT_PARAM: {"initial": 25.01628206523205, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 200, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Adjust base stock based on expected demand
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order-up-to level
    order_up_to = max(adjusted_base_stock, expected_lead_time_demand + safety_stock)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Smooth ordering with a minimum order threshold
    min_order_threshold = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0, "max": 50, "type": "float"}
    if order_amount < min_order_threshold:
        order_amount = 0

    return order_amount
