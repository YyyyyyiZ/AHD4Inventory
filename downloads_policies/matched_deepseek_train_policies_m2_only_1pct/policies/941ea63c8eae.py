# policy_hash: 941ea63c8eae2899bcd54611ca5b1733fd1128ed02d91d7476ccbcea41f13017
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 760.93
# best_prompt_performance: 760.93
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_013058.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 625.0  # OPT_PARAM: {"initial": 625.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 89.63297462043215  # OPT_PARAM: {"initial": 89.63297462043215, "min": 30, "max": 120, "type": "float"}
    demand_estimate = 119.7345732121946  # OPT_PARAM: {"initial": 119.7345732121946, "min": 80, "max": 120, "type": "float"}
    max_order = 95.9241624194834  # OPT_PARAM: {"initial": 95.9241624194834, "min": 80, "max": 200, "type": "float"}
    min_order = 18.407064913811965  # OPT_PARAM: {"initial": 18.407064913811965, "min": 0, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply order smoothing and constraints
    order_amount = min(order_amount, max_order)
    order_amount = max(order_amount, min_order)

    # Round to nearest integer since order amount must be integer
    return order_amount
