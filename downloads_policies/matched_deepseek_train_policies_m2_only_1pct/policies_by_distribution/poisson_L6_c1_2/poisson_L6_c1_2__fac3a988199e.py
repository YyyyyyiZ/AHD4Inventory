# policy_hash: fac3a988199e2862ece61bc00c5f10dd31bdfac5c8e938c72f62a3f30ec1e515
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 20
# source_prompt_files: 1
# best_target_performance: 1218.1
# best_prompt_performance: 1218.7
# best_rel_error_pct: 0.049257
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_012635.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 750.0  # OPT_PARAM: {"initial": 750.0, "min": 500, "max": 1200, "type": "float"}
    safety_stock = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 0, "max": 100, "type": "float"}
    demand_estimate = 114.2135553845174  # OPT_PARAM: {"initial": 114.2135553845174, "min": 80, "max": 120, "type": "float"}
    max_order = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 200, "type": "float"}
    min_order = 20.1  # OPT_PARAM: {"initial": 20.1, "min": 0, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply order smoothing and limits
    if order_amount > 0:
        order_amount = max(min_order, min(order_amount, max_order))

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
