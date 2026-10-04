# policy_hash: f983c823c39c988078b901a6fe355058b151ee71931a949c3334901594b9e82c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1590.22
# best_prompt_performance: 1582.0
# best_rel_error_pct: 0.516910
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251224_054105.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Demand statistics (pre-calculated from historical data)
    avg_demand = 100.0  # Approximate average from the data
    lead_time = 6

    # Optimizable parameters
    base_stock_multiplier = 9.653496750590897  # OPT_PARAM: {"initial": 9.653496750590897, "min": 4.0, "max": 10.0, "type": "float"}
    safety_factor = 1.379311684967127  # OPT_PARAM: {"initial": 1.379311684967127, "min": 0.5, "max": 2.5, "type": "float"}
    smoothing_factor = 0.11449671843510342  # OPT_PARAM: {"initial": 0.11449671843510342, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate base stock level
    safety_stock = safety_factor * avg_demand * (lead_time ** 0.5)
    base_stock = base_stock_multiplier * avg_demand + safety_stock

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate desired order with smoothing
    desired_order = max(0, base_stock - inventory_position)
    order_amount = smoothing_factor * desired_order

    # Round to nearest integer (orders must be integer quantities)
    return order_amount
