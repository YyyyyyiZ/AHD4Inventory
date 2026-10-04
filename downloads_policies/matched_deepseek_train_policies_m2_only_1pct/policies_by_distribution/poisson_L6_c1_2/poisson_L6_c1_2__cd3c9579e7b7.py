# policy_hash: cd3c9579e7b7ee143043dcc9d33a8b009d7fe9cad83da8a732ef4587e61c92e9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 762.35
# best_prompt_performance: 762.39
# best_rel_error_pct: 0.005247
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_022909.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 480.0  # OPT_PARAM: {"initial": 480.0, "min": 300, "max": 700, "type": "float"}
    safety_stock = 86.97547432010288  # OPT_PARAM: {"initial": 86.97547432010288, "min": 0, "max": 100, "type": "float"}
    demand_forecast = 119.44009974214444  # OPT_PARAM: {"initial": 119.44009974214444, "min": 80, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_forecast * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Order up to target, but ensure non-negative
    order_amount = max(0, target_position - inventory_position)

    # Cap order amount to avoid excessive ordering
    max_order = 96.00039730435219  # OPT_PARAM: {"initial": 96.00039730435219, "min": 80, "max": 200, "type": "float"}
    order_amount = min(order_amount, max_order)

    return order_amount
