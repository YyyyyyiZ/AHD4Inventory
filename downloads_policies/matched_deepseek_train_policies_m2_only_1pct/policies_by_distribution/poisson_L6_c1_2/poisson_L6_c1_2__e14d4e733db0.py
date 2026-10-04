# policy_hash: e14d4e733db01e3bc8ac118ce466a30ec779999445da45e7b25142f6c296e2b8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 22
# source_prompt_files: 2
# best_target_performance: 761.01
# best_prompt_performance: 761.01
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_022456.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 580.0  # OPT_PARAM: {"initial": 580.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 88.69197201244371  # OPT_PARAM: {"initial": 88.69197201244371, "min": 20, "max": 100, "type": "float"}
    demand_forecast = 119.93543417623448  # OPT_PARAM: {"initial": 119.93543417623448, "min": 80, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_forecast * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Order up to target, but ensure non-negative
    order_amount = max(0, target_position - inventory_position)

    # Cap order amount to avoid excessive ordering
    max_order = 95.90979529893087  # OPT_PARAM: {"initial": 95.90979529893087, "min": 80, "max": 200, "type": "float"}
    order_amount = min(order_amount, max_order)

    return order_amount
