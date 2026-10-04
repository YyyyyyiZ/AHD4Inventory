# policy_hash: 18211c1d4f90ccb48616f769008f9b76e8bae7da3a03cfc54e6354e448fe0ce8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 7
# source_prompt_files: 2
# best_target_performance: 1233.44
# best_prompt_performance: 1233.44
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_011748.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 625.0  # OPT_PARAM: {"initial": 625.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 55.5999999999941  # OPT_PARAM: {"initial": 55.5999999999941, "min": 20, "max": 100, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}
    max_order = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 200, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply order smoothing to reduce volatility
    smoothing_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}
    order_amount = smoothing_factor * order_amount

    # Cap order amount
    order_amount = min(order_amount, max_order)

    # Round to nearest integer (since order amounts must be integers)
    order_amount = int(round(order_amount))

    return order_amount
